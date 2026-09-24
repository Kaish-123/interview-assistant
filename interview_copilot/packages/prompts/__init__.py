"""Prompt library stores — tabs.json + setup_profiles.json contracts."""

from interview_copilot.packages.prompts.profiles import SetupProfilesStore
from interview_copilot.packages.prompts.protocol import PromptStore
from interview_copilot.packages.prompts.tabs import PromptTabsStore

__all__ = [
    "PromptStore",
    "PromptTabsStore",
    "SetupProfilesStore",
]
