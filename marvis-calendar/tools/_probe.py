import os
import unicodedata

d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("目录:", d)
for f in os.listdir(d):
    if f.endswith(".iss"):
        print("repr:", repr(f))
        print("  NFC == 源码字面量:", unicodedata.normalize("NFC", f) == "鑫哥日历.iss")
        print("  codepoints:", [hex(ord(c)) for c in f])
