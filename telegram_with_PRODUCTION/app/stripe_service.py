"""
Stripe Payment Integration
"""
import stripe
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings, PLANS
from app.models import User, Subscription, PlanType, SubscriptionStatus

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Stripe Payment Service"""
    
    @staticmethod
    def get_price_id(plan: str) -> Optional[str]:
        """Get Stripe price ID for a plan"""
        price_map = {
            "starter": settings.STRIPE_PRICE_STARTER,
            "pro": settings.STRIPE_PRICE_PRO,
            "business": settings.STRIPE_PRICE_BUSINESS,
        }
        return price_map.get(plan)
    
    @staticmethod
    async def create_customer(user: User) -> str:
        """Create a Stripe customer for user"""
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            metadata={
                "user_id": str(user.id)
            }
        )
        return customer.id
    
    @staticmethod
    async def create_checkout_session(
        user: User,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create Stripe checkout session for subscription"""
        
        price_id = StripeService.get_price_id(plan)
        if not price_id:
            raise ValueError(f"Invalid plan: {plan}")
        
        # Create or get customer
        customer_id = user.stripe_customer_id
        if not customer_id:
            customer_id = await StripeService.create_customer(user)
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user.id),
                "plan": plan
            },
            subscription_data={
                "metadata": {
                    "user_id": str(user.id),
                    "plan": plan
                }
            }
        )
        
        return {
            "session_id": session.id,
            "url": session.url
        }
    
    @staticmethod
    async def create_billing_portal_session(user: User, return_url: str) -> str:
        """Create Stripe billing portal session"""
        if not user.stripe_customer_id:
            raise ValueError("User has no Stripe customer")
        
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url
        )
        
        return session.url
    
    @staticmethod
    async def cancel_subscription(subscription_id: str) -> bool:
        """Cancel a subscription at period end"""
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    async def handle_webhook(payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")
        
        return {
            "type": event["type"],
            "data": event["data"]["object"]
        }


async def process_subscription_event(
    db: AsyncSession,
    event_type: str,
    data: Dict[str, Any]
):
    """Process Stripe subscription webhook events"""
    
    if event_type == "checkout.session.completed":
        # New subscription created
        user_id = data.get("metadata", {}).get("user_id")
        plan = data.get("metadata", {}).get("plan")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        
        if user_id and plan:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if user:
                # Update user
                user.stripe_customer_id = customer_id
                user.plan = PlanType(plan)
                user.subscription_status = SubscriptionStatus.ACTIVE
                
                # Create subscription record
                subscription = Subscription(
                    user_id=user.id,
                    stripe_subscription_id=subscription_id,
                    plan=PlanType(plan),
                    status=SubscriptionStatus.ACTIVE
                )
                db.add(subscription)
                await db.commit()
    
    elif event_type == "customer.subscription.updated":
        subscription_id = data.get("id")
        status = data.get("status")
        cancel_at_period_end = data.get("cancel_at_period_end", False)
        
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            # Map Stripe status to our status
            status_map = {
                "active": SubscriptionStatus.ACTIVE,
                "past_due": SubscriptionStatus.PAST_DUE,
                "canceled": SubscriptionStatus.CANCELED,
                "trialing": SubscriptionStatus.TRIALING,
            }
            subscription.status = status_map.get(status, SubscriptionStatus.INACTIVE)
            subscription.cancel_at_period_end = cancel_at_period_end
            
            # Update user status
            result = await db.execute(select(User).where(User.id == subscription.user_id))
            user = result.scalar_one_or_none()
            if user:
                user.subscription_status = subscription.status
            
            await db.commit()
    
    elif event_type == "customer.subscription.deleted":
        subscription_id = data.get("id")
        
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            
            # Downgrade user to free plan
            result = await db.execute(select(User).where(User.id == subscription.user_id))
            user = result.scalar_one_or_none()
            if user:
                user.plan = PlanType.FREE
                user.subscription_status = SubscriptionStatus.INACTIVE
            
            await db.commit()

