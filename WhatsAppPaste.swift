#!/usr/bin/env swift
// WhatsApp Photo Paste - Copies image DATA (not files) and pastes
// Compile: swiftc -o WhatsAppPaste WhatsAppPaste.swift
// Run: ./WhatsAppPaste

import Cocoa
import Foundation

let photosFolder = NSString(string: "~/Desktop/photos_to_paste").expandingTildeInPath
let imageExtensions = ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "heic"]

func notify(_ title: String, _ message: String) {
    let script = "display notification \"\(message)\" with title \"\(title)\""
    var error: NSDictionary?
    NSAppleScript(source: script)?.executeAndReturnError(&error)
}

func copyImageToClipboard(_ path: String) -> Bool {
    guard let image = NSImage(contentsOfFile: path) else {
        return false
    }
    
    let pasteboard = NSPasteboard.general
    pasteboard.clearContents()
    pasteboard.writeObjects([image])
    return true
}

func paste() {
    let script = "tell application \"System Events\" to keystroke \"v\" using command down"
    var error: NSDictionary?
    NSAppleScript(source: script)?.executeAndReturnError(&error)
}

func pressEnter() {
    let script = "tell application \"System Events\" to keystroke return"
    var error: NSDictionary?
    NSAppleScript(source: script)?.executeAndReturnError(&error)
}

// Main
let fileManager = FileManager.default

guard fileManager.fileExists(atPath: photosFolder) else {
    notify("Error", "Folder not found!")
    exit(1)
}

guard let files = try? fileManager.contentsOfDirectory(atPath: photosFolder) else {
    notify("Error", "Cannot read folder")
    exit(1)
}

let imageFiles = files.filter { file in
    let ext = (file as NSString).pathExtension.lowercased()
    return imageExtensions.contains(ext)
}.sorted()

guard !imageFiles.isEmpty else {
    notify("Paste Photos", "No images found")
    exit(0)
}

notify("Paste Photos", "Pasting \(imageFiles.count) photos...")

// Small delay to let user focus
Thread.sleep(forTimeInterval: 0.5)

for (index, file) in imageFiles.enumerated() {
    let fullPath = (photosFolder as NSString).appendingPathComponent(file)
    print("[\(index + 1)/\(imageFiles.count)] \(file)")
    
    if copyImageToClipboard(fullPath) {
        paste()
        Thread.sleep(forTimeInterval: 0.3)
        pressEnter()
        Thread.sleep(forTimeInterval: 0.5)
    }
}

notify("Done!", "Pasted \(imageFiles.count) photos!")
