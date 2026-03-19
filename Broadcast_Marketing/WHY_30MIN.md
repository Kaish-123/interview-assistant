# Why messages are sent every 30 minutes

## Reason we use 30 minutes

1. **WhatsApp rate limits** – Sending too many messages in a short time can trigger limits or temporary blocks. Spacing runs to **every 30 minutes** keeps each run smaller and reduces the chance of being flagged as spam.

2. **Account safety** – WhatsApp may restrict or ban accounts that send a lot of messages very quickly. A 30‑minute interval is a safe balance between “frequent” and “not suspicious.”

3. **Reach without overload** – For marketing, 30 minutes is frequent enough to reach people regularly (e.g. twice per hour if you want), without hammering the same contacts too often.

4. **Technical limits** – Sending uses WhatsApp Web (browser). Each run opens the browser and sends to your list; doing this every few minutes would be heavy on the machine and more likely to hit WhatsApp’s limits.

So: **30 minutes = frequent enough for marketing, but safe for your account and within typical rate limits.**

## Changing the interval

The schedule is set in `com.broadcast.marketing.send.plist`: `StartInterval` is in **seconds**.

- **30 minutes** = `1800` (current)
- **15 minutes** = `900`
- **1 hour** = `3600`

After editing the plist, run:

```bash
launchctl unload ~/Library/LaunchAgents/com.broadcast.marketing.send.plist
./run.sh install-send-schedule
```

**Recommendation:** Keep at least 15–30 minutes between runs to stay on the safe side with WhatsApp.
