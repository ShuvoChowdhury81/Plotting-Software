import base64

# Base64 string for a small, sharp black checkmark
b64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAABTSURBVDhPYxzBQAQMxP/pZg+2AhiI1Y5VA2bEWMDEyMT0H8wmg1E1kG0AzRykBgBdgOw2ZAF0A7EahDQAYiL1AKMBtHSAkQFIQzQpAA2hB5gYGAA/VxE/sTj2lwAAAABJRU5ErkJggg=="

with open("check.png", "wb") as f:
    f.write(base64.b64decode(b64))
print("Successfully generated check.png")
