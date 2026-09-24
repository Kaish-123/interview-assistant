#!/usr/bin/env python3
"""Build and sign the Share Call Slots Apple Shortcut."""

from __future__ import annotations

import plistlib
import subprocess
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OBJ = "\ufffc"
CALL_CALENDAR = "saudagercash14@gmail.com"


def uid() -> str:
    return str(uuid.uuid4()).upper()


def action(identifier: str, **params) -> dict:
    return {
        "WFWorkflowActionIdentifier": identifier,
        "WFWorkflowActionParameters": params,
    }


def var_ref(name: str) -> dict:
    return {
        "Value": {"Type": "Variable", "VariableName": name},
        "WFSerializationType": "WFTextTokenAttachment",
    }


def out_ref(output_uuid: str, output_name: str) -> dict:
    return {
        "Value": {
            "OutputUUID": output_uuid,
            "OutputName": output_name,
            "Type": "ActionOutput",
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def cond_input(ref: dict) -> dict:
    return {"Type": "Variable", "Variable": ref}


def text_with(*parts) -> dict:
    string = ""
    attachments: dict[str, dict] = {}
    for part in parts:
        if isinstance(part, str):
            string += part
            continue
        start = len(string)
        string += OBJ
        kind = part[0]
        if kind == "var":
            attachments[f"{{{start}, 1}}"] = {
                "Type": "Variable",
                "VariableName": part[1],
            }
        else:
            attachments[f"{{{start}, 1}}"] = {
                "Type": "ActionOutput",
                "OutputUUID": part[1],
                "OutputName": part[2],
            }
    return {
        "Value": {"string": string, "attachmentsByRange": attachments},
        "WFSerializationType": "WFTextTokenString",
    }


def duration(magnitude: float, unit: str) -> dict:
    return {
        "Value": {"Magnitude": magnitude, "Unit": unit},
        "WFSerializationType": "WFQuantityFieldValue",
    }


def set_var(name: str, ref: dict | None = None) -> dict:
    params = {"WFVariableName": name}
    if ref is not None:
        params["WFInput"] = ref
    return action("is.workflow.actions.setvariable", **params)


def get_var(name: str) -> dict:
    return action("is.workflow.actions.getvariable", WFVariable=var_ref(name))


def number(value, output_name: str | None = None) -> dict:
    params = {"WFNumberActionNumber": value}
    if output_name:
        params["UUID"] = uid()
        params["CustomOutputName"] = output_name
    return action("is.workflow.actions.number", **params)


def comment(text: str) -> dict:
    return action("is.workflow.actions.comment", WFCommentActionText=text)


def ask_date(prompt: str, default_ref: dict) -> dict:
    return action(
        "is.workflow.actions.ask",
        UUID=uid(),
        CustomOutputName="Chosen Date",
        WFAskActionPrompt=prompt,
        WFInputType="Date",
        WFAskActionDefaultAnswerDateAndTime=default_ref,
    )


def adjust(date_ref: dict, operation: str, mag: float | None = None, unit: str = "hr", **extra) -> dict:
    params = {
        "UUID": uid(),
        "CustomOutputName": extra.pop("name", "Adjusted Date"),
        "WFDate": date_ref,
        "WFAdjustOperation": operation,
    }
    if mag is not None:
        params["WFDuration"] = duration(mag, unit)
    params.update(extra)
    return action("is.workflow.actions.adjustdate", **params)


def format_date(date_ref: dict, *, date_style: str, time_style: str, custom: str | None = None, name: str = "Formatted Date") -> dict:
    params = {
        "UUID": uid(),
        "CustomOutputName": name,
        "WFDate": date_ref,
        "WFDateFormatStyle": date_style,
        "WFTimeFormatStyle": time_style,
    }
    if custom:
        params["WFDateFormat"] = custom
        params["WFDateFormatString"] = custom
    return action("is.workflow.actions.format.date", **params)


def time_between(first: dict, second: dict, unit: str = "Minutes", name: str = "Gap Minutes") -> dict:
    params = {
        "UUID": uid(),
        "CustomOutputName": name,
        "WFTimeUntilFromDate": first,
        "WFInput": second,
        "WFTimeUntilUnit": unit,
    }
    return action("is.workflow.actions.gettimebetweendates", **params)


def if_start(group: str, condition: int, input_ref: dict, **extra) -> dict:
    params = {
        "GroupingIdentifier": group,
        "WFControlFlowMode": 0,
        "WFCondition": condition,
        "WFInput": cond_input(input_ref),
    }
    params.update(extra)
    return action("is.workflow.actions.conditional", **params)


def if_end(group: str, mode: int = 2) -> dict:
    return action(
        "is.workflow.actions.conditional",
        GroupingIdentifier=group,
        WFControlFlowMode=mode,
    )


def repeat_start(group: str, count) -> dict:
    params = {
        "UUID": uid(),
        "GroupingIdentifier": group,
        "WFControlFlowMode": 0,
        "WFRepeatCount": count,
    }
    return action("is.workflow.actions.repeat.count", **params)


def repeat_end(group: str) -> dict:
    return action(
        "is.workflow.actions.repeat.count",
        UUID=uid(),
        GroupingIdentifier=group,
        WFControlFlowMode=2,
    )


def each_start(group: str, items: dict) -> dict:
    return action(
        "is.workflow.actions.repeat.each",
        UUID=uid(),
        GroupingIdentifier=group,
        WFControlFlowMode=0,
        WFInput=items,
    )


def each_end(group: str) -> dict:
    return action(
        "is.workflow.actions.repeat.each",
        UUID=uid(),
        GroupingIdentifier=group,
        WFControlFlowMode=2,
    )


def menu_start(group: str, prompt: str, items: list[str]) -> dict:
    return action(
        "is.workflow.actions.choosefrommenu",
        GroupingIdentifier=group,
        WFControlFlowMode=0,
        WFMenuPrompt=prompt,
        WFMenuItems=items,
    )


def menu_item(group: str, title: str) -> dict:
    return action(
        "is.workflow.actions.choosefrommenu",
        GroupingIdentifier=group,
        WFControlFlowMode=1,
        WFMenuItemTitle=title,
    )


def menu_end(group: str) -> dict:
    return action(
        "is.workflow.actions.choosefrommenu",
        GroupingIdentifier=group,
        WFControlFlowMode=2,
    )


def event_property(prop: str, name: str) -> dict:
    return action(
        "is.workflow.actions.properties.calendarevents",
        UUID=uid(),
        CustomOutputName=name,
        WFContentItemPropertyName=prop,
        WFInput=var_ref("Repeat Item"),
    )


def _calendar_is_row() -> dict:
    return {
        "Operator": 4,
        "Property": "Calendar",
        "Removable": True,
        "Values": {
            "String": CALL_CALENDAR,
            "Enumeration": {
                "Value": CALL_CALENDAR,
                "WFSerializationType": "WFStringSubstitutableState",
            },
            "Unit": 4,
        },
    }


def find_upcoming_events() -> dict:
    return action(
        "is.workflow.actions.filter.calendarevents",
        UUID=uid(),
        CustomOutputName="Calendar Events",
        WFContentItemSortProperty="Start Date",
        WFContentItemSortOrder="Oldest First",
        WFContentItemLimitEnabled=True,
        WFContentItemLimit=150,
        WFContentItemFilter={
            "Value": {
                "WFActionParameterFilterPrefix": 0,
                "WFContentPredicateBoundedDate": False,
                "WFActionParameterFilterTemplates": [
                    {
                        "Operator": 1000,
                        "Property": "Start Date",
                        "Removable": True,
                        "Values": {"Number": 8, "Unit": 16384},
                    },
                    {
                        "Operator": 1001,
                        "Property": "Start Date",
                        "Removable": True,
                        "Values": {"Number": 1, "Unit": 16384},
                    },
                    {
                        "Operator": 1000,
                        "Property": "End Date",
                        "Removable": True,
                        "Values": {"Number": 8, "Unit": 16384},
                    },
                ],
            },
            "WFSerializationType": "WFContentPredicateTableTemplate",
        },
    )


def filter_gmail_calendar(events_ref: dict) -> dict:
    return action(
        "is.workflow.actions.filter.calendarevents",
        UUID=uid(),
        CustomOutputName="Gmail Events",
        WFContentItemInputParameter=events_ref,
        WFContentItemSortProperty="Start Date",
        WFContentItemSortOrder="Oldest First",
        WFContentItemFilter={
            "Value": {
                "WFActionParameterFilterPrefix": 1,
                "WFContentPredicateBoundedDate": False,
                "WFActionParameterFilterTemplates": [_calendar_is_row()],
            },
            "WFSerializationType": "WFContentPredicateTableTemplate",
        },
    )


def emit_slot(actions: list[dict], start_ref: dict, end_ref: dict) -> None:
    """Append a WhatsApp bullet if the gap is at least 30 minutes."""
    gap = time_between(start_ref, end_ref, name="Gap Minutes")
    actions.append(gap)
    group = uid()
    actions.append(
        if_start(
            group,
            3,
            out_ref(gap["WFWorkflowActionParameters"]["UUID"], "Gap Minutes"),
            WFNumberValue="15",
        )
    )
    start_fmt = format_date(
        start_ref, date_style="None", time_style="Short", name="Slot Start"
    )
    end_fmt = format_date(
        end_ref, date_style="None", time_style="Short", name="Slot End"
    )
    actions.extend([start_fmt, end_fmt])
    line = action(
        "is.workflow.actions.gettext",
        UUID=uid(),
        CustomOutputName="Slot Line",
        WFTextActionText=text_with(
            "• ",
            ("out", start_fmt["WFWorkflowActionParameters"]["UUID"], "Slot Start"),
            " – ",
            ("out", end_fmt["WFWorkflowActionParameters"]["UUID"], "Slot End"),
            " IST",
        ),
    )
    actions.append(line)
    join = action(
        "is.workflow.actions.gettext",
        UUID=uid(),
        CustomOutputName="Day Lines Joined",
        WFTextActionText=text_with(
            ("var", "DayLines"),
            "\n",
            ("out", line["WFWorkflowActionParameters"]["UUID"], "Slot Line"),
        ),
    )
    actions.append(join)
    actions.append(set_var("DayLines", out_ref(join["WFWorkflowActionParameters"]["UUID"], "Day Lines Joined")))
    actions.append(if_end(group))


def build_actions() -> list[dict]:
    actions: list[dict] = []
    actions.append(
        comment(
            "Share Call Slots from saudagercash14@gmail.com.\n"
            "One night: 5:00 PM IST to 5:00 AM IST. Date picker defaults to today.\n"
            "Lists exact free gaps between meetings for WhatsApp."
        )
    )

    today = action(
        "is.workflow.actions.date",
        UUID=uid(),
        CustomOutputName="Current Date",
        WFDateActionMode="Current Date",
    )
    actions.append(today)
    chosen = ask_date(
        "Night of 5:00 PM IST (runs until 5:00 AM next day). Leave as today.",
        out_ref(today["WFWorkflowActionParameters"]["UUID"], "Current Date"),
    )
    actions.extend(
        [
            chosen,
            set_var("Day", out_ref(chosen["WFWorkflowActionParameters"]["UUID"], "Chosen Date")),
        ]
    )

    empty = action("is.workflow.actions.gettext", UUID=uid(), CustomOutputName="Empty", WFTextActionText="")
    actions.extend([empty, set_var("EmptyText", out_ref(empty["WFWorkflowActionParameters"]["UUID"], "Empty"))])
    actions.append(set_var("DayLines", var_ref("EmptyText")))

    midnight = adjust(var_ref("Day"), "Get Start of Day", name="Midnight")
    actions.extend([midnight, set_var("Midnight", out_ref(midnight["WFWorkflowActionParameters"]["UUID"], "Midnight"))])
    window_start = adjust(var_ref("Midnight"), "Add", 17, "hr", name="Window Start")
    actions.extend(
        [window_start, set_var("WindowStart", out_ref(window_start["WFWorkflowActionParameters"]["UUID"], "Window Start"))]
    )
    window_end = adjust(var_ref("WindowStart"), "Add", 12, "hr", name="Window End")
    actions.extend(
        [window_end, set_var("WindowEnd", out_ref(window_end["WFWorkflowActionParameters"]["UUID"], "Window End"))]
    )
    actions.append(set_var("Cursor", var_ref("WindowStart")))

    start_label = format_date(
        var_ref("WindowStart"), date_style="Medium", time_style="Short", name="Window Start Label"
    )
    end_label = format_date(
        var_ref("WindowEnd"), date_style="Medium", time_style="Short", name="Window End Label"
    )
    actions.extend([start_label, end_label])
    header = action(
        "is.workflow.actions.gettext",
        UUID=uid(),
        CustomOutputName="Header",
        WFTextActionText=text_with(
            "Available for calls\n",
            "Calendar: saudagercash14@gmail.com\n",
            "Window: ",
            ("out", start_label["WFWorkflowActionParameters"]["UUID"], "Window Start Label"),
            " – ",
            ("out", end_label["WFWorkflowActionParameters"]["UUID"], "Window End Label"),
            " IST\n\n",
            "Pick a slot and reply here.\n",
        ),
    )
    actions.extend([header, set_var("Message", out_ref(header["WFWorkflowActionParameters"]["UUID"], "Header"))])

    events = find_upcoming_events()
    gmail_events = filter_gmail_calendar(
        out_ref(events["WFWorkflowActionParameters"]["UUID"], "Calendar Events")
    )
    actions.extend(
        [
            events,
            gmail_events,
            set_var("AllEvents", out_ref(gmail_events["WFWorkflowActionParameters"]["UUID"], "Gmail Events")),
        ]
    )

    each_group = uid()
    actions.append(each_start(each_group, var_ref("AllEvents")))

    start_prop = event_property("Start Date", "Event Start")
    end_prop = event_property("End Date", "Event End")
    actions.extend(
        [
            start_prop,
            set_var("EvStart", out_ref(start_prop["WFWorkflowActionParameters"]["UUID"], "Event Start")),
            end_prop,
            set_var("EvEnd", out_ref(end_prop["WFWorkflowActionParameters"]["UUID"], "Event End")),
        ]
    )

    # Skip events that start after the window: time(WindowEnd, EvStart) > 0
    after_window = time_between(var_ref("WindowEnd"), var_ref("EvStart"), name="Starts After Window")
    actions.append(after_window)
    skip_start = uid()
    actions.append(
        if_start(
            skip_start,
            2,
            out_ref(after_window["WFWorkflowActionParameters"]["UUID"], "Starts After Window"),
            WFNumberValue="0",
        )
    )
    # If true: skip (do nothing)
    actions.append(if_end(skip_start, 1))

    # Skip events that ended before the window: time(EvEnd, WindowStart) > 0
    before_window = time_between(var_ref("EvEnd"), var_ref("WindowStart"), name="Ends Before Window")
    actions.append(before_window)
    skip_end = uid()
    actions.append(
        if_start(
            skip_end,
            2,
            out_ref(before_window["WFWorkflowActionParameters"]["UUID"], "Ends Before Window"),
            WFNumberValue="0",
        )
    )
    actions.append(if_end(skip_end, 1))

    # Clamp start: if WindowStart after EvStart, EvStart = WindowStart
    clamp_start_gap = time_between(var_ref("EvStart"), var_ref("WindowStart"), name="Clamp Start")
    actions.append(clamp_start_gap)
    clamp_s = uid()
    actions.append(
        if_start(
            clamp_s,
            2,
            out_ref(clamp_start_gap["WFWorkflowActionParameters"]["UUID"], "Clamp Start"),
            WFNumberValue="0",
        )
    )
    actions.append(set_var("EvStart", var_ref("WindowStart")))
    actions.append(if_end(clamp_s))

    clamp_end_gap = time_between(var_ref("WindowEnd"), var_ref("EvEnd"), name="Clamp End")
    actions.append(clamp_end_gap)
    clamp_e = uid()
    actions.append(
        if_start(
            clamp_e,
            3,
            out_ref(clamp_end_gap["WFWorkflowActionParameters"]["UUID"], "Clamp End"),
            WFNumberValue="0",
        )
    )
    actions.append(set_var("EvEnd", var_ref("WindowEnd")))
    actions.append(if_end(clamp_e))

    # If EvStart is after Cursor, emit Cursor → EvStart
    free_gap = time_between(var_ref("Cursor"), var_ref("EvStart"), name="Free Gap")
    actions.append(free_gap)
    emit_if = uid()
    actions.append(
        if_start(
            emit_if,
            3,
            out_ref(free_gap["WFWorkflowActionParameters"]["UUID"], "Free Gap"),
            WFNumberValue="15",
        )
    )
    emit_slot(actions, var_ref("Cursor"), var_ref("EvStart"))
    actions.append(if_end(emit_if))

    # Advance cursor if EvEnd is after Cursor
    advance_gap = time_between(var_ref("Cursor"), var_ref("EvEnd"), name="Advance Gap")
    actions.append(advance_gap)
    adv = uid()
    actions.append(
        if_start(
            adv,
            2,
            out_ref(advance_gap["WFWorkflowActionParameters"]["UUID"], "Advance Gap"),
            WFNumberValue="0",
        )
    )
    actions.append(set_var("Cursor", var_ref("EvEnd")))
    actions.append(if_end(adv))

    actions.append(if_end(skip_end))
    actions.append(if_end(skip_start))
    actions.append(each_end(each_group))

    # Tail slot after last event
    tail = time_between(var_ref("Cursor"), var_ref("WindowEnd"), name="Tail Gap")
    actions.append(tail)
    tail_if = uid()
    actions.append(
        if_start(
            tail_if,
            3,
            out_ref(tail["WFWorkflowActionParameters"]["UUID"], "Tail Gap"),
            WFNumberValue="15",
        )
    )
    emit_slot(actions, var_ref("Cursor"), var_ref("WindowEnd"))
    actions.append(if_end(tail_if))

    line_chars = action(
        "is.workflow.actions.count",
        UUID=uid(),
        CustomOutputName="Day Line Chars",
        Input=var_ref("DayLines"),
        WFCountType="Characters",
    )
    actions.append(line_chars)
    has_lines = uid()
    actions.append(
        if_start(
            has_lines,
            2,
            out_ref(line_chars["WFWorkflowActionParameters"]["UUID"], "Day Line Chars"),
            WFNumberValue="0",
        )
    )
    with_slots = action(
        "is.workflow.actions.gettext",
        UUID=uid(),
        CustomOutputName="Final Message",
        WFTextActionText=text_with(
            ("var", "Message"),
            "\n",
            ("var", "DayLines"),
            "\n",
        ),
    )
    actions.append(with_slots)
    actions.append(set_var("Message", out_ref(with_slots["WFWorkflowActionParameters"]["UUID"], "Final Message")))
    actions.append(if_end(has_lines, 1))
    none = action(
        "is.workflow.actions.gettext",
        UUID=uid(),
        CustomOutputName="Empty Night",
        WFTextActionText=text_with(
            ("var", "Message"),
            "\nNo free slots in this window.\n",
        ),
    )
    actions.append(none)
    actions.append(set_var("Message", out_ref(none["WFWorkflowActionParameters"]["UUID"], "Empty Night")))
    actions.append(if_end(has_lines))

    actions.append(get_var("Message"))
    actions.append(action("is.workflow.actions.setclipboard", WFInput=var_ref("Message")))

    encoded = action(
        "is.workflow.actions.urlencode",
        UUID=uid(),
        CustomOutputName="Encoded Message",
        WFEncodeMode="Encode",
        WFInput=var_ref("Message"),
    )
    actions.append(encoded)
    wa = action(
        "is.workflow.actions.gettext",
        UUID=uid(),
        CustomOutputName="WhatsApp URL",
        WFTextActionText=text_with(
            "whatsapp://send?text=",
            ("out", encoded["WFWorkflowActionParameters"]["UUID"], "Encoded Message"),
        ),
    )
    actions.append(wa)
    actions.append(
        action(
            "is.workflow.actions.openurl",
            UUID=uid(),
            WFInput=out_ref(wa["WFWorkflowActionParameters"]["UUID"], "WhatsApp URL"),
        )
    )
    actions.append(action("is.workflow.actions.share", WFInput=var_ref("Message")))
    return actions


def build_workflow() -> dict:
    return {
        "WFWorkflowClientVersion": "2702.0.0",
        "WFWorkflowClientRelease": "5.0",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowName": "Share Call Slots",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 4292093695,
            "WFWorkflowIconGlyphNumber": 59769,
        },
        "WFWorkflowTypes": ["NCWidget", "Watch", "MenuBar"],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowOutputContentItemClasses": ["WFStringContentItem"],
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowHasShortcutInputVariables": False,
        "WFWorkflowImportQuestions": [],
        "WFWorkflowActions": build_actions(),
    }


def main() -> None:
    workflow = build_workflow()
    plist_path = ROOT / "Share Call Slots.plist"
    unsigned = ROOT / "Share Call Slots.unsigned.shortcut"
    signed = ROOT / "out" / "Share Call Slots.shortcut"
    plist_path.write_bytes(plistlib.dumps(workflow, fmt=plistlib.FMT_XML))
    unsigned.write_bytes(plistlib.dumps(workflow, fmt=plistlib.FMT_BINARY))
    signed.parent.mkdir(exist_ok=True)
    print(f"Wrote {plist_path} ({len(workflow['WFWorkflowActions'])} actions)")
    subprocess.run(
        [
            "shortcuts",
            "sign",
            "--mode",
            "anyone",
            "--input",
            str(unsigned),
            "--output",
            str(signed),
        ],
        check=True,
    )
    print(f"Signed {signed}")


if __name__ == "__main__":
    main()
