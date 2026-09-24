"""
Phase 1 Milestone 6 — session/prompts harness.

  python3 -m interview_copilot.packages.session.harness
"""

from __future__ import annotations

from interview_copilot.packages.prompts import PromptTabsStore, SetupProfilesStore
from interview_copilot.packages.session import (
    AUTO_SAVE_TITLE,
    ChatHistoryStore,
    UIPreferencesStore,
)
from interview_copilot.shared.config import get_paths, get_settings
from interview_copilot.shared.logging import setup_logging


def main() -> None:
    settings = get_settings()
    paths = get_paths()
    setup_logging(settings, force=True)

    print("Interview Copilot — Phase 1 Milestone 6 (Session + Prompts)")
    print(f"  data_dir:     {paths.data_dir}")
    print(f"  chats:        {paths.chats_json}")
    print(f"  tabs:         {paths.tabs_json}")
    print(f"  profiles:     {paths.setup_profiles_json}")
    print(f"  ui_prefs:     {paths.ui_prefs_json}")

    chats = ChatHistoryStore()
    print(f"  chat count:   {len(chats.sessions)}")
    auto = chats.find_autosave()
    print(f"  autosave:     {'yes' if auto else 'no'} ({AUTO_SAVE_TITLE})")

    tabs = PromptTabsStore()
    print(f"  tabs:         {tabs.get_tab_count()}")
    for i in range(tabs.get_tab_count()):
        print(f"    - {tabs.get_tab_name(i)} ({tabs.get_subtab_count(i)} subtabs)")

    profiles = SetupProfilesStore()
    print(f"  profiles:     {profiles.list_names()}")

    prefs = UIPreferencesStore().load()
    print(f"  ui_prefs keys:{sorted(prefs.keys())}")


if __name__ == "__main__":
    main()
