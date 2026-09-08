from pathlib import Path
import re

# CHANGE THIS to the actual HTML filename
file_path = Path("index.html")

text = file_path.read_text(encoding="utf-8")

# --------------------------------------------------
# BACKUP FIRST
# --------------------------------------------------
backup = file_path.with_suffix(file_path.suffix + ".backup")
backup.write_text(text, encoding="utf-8")

print(f"Backup created: {backup}")


# --------------------------------------------------
# 1. Remove empty Kirki styles
# --------------------------------------------------
text = text.replace(
    '<style id="kirki-inline-styles"></style>',
    ''
)


# --------------------------------------------------
# 2. Remove invalid CSS declaration
# --------------------------------------------------
text = text.replace(
    'font-size: bolder;',
    ''
)


# --------------------------------------------------
# 3. Remove useless CSS comments
# --------------------------------------------------
for comment in [
    '/* display: flex; */',
    '/* -webkit-box-align: center; */',
    '/* justify-content: inherit; */',
]:
    text = text.replace(comment, '')


# --------------------------------------------------
# 4. Remove duplicate Mailchimp scripts
#    KEEP FIRST ONE
# --------------------------------------------------
mailchimp_pattern = re.compile(
    r'<script\s+async=""\s+src="https://chimpstatic\.com/'
    r'mcjs-connected/js/users/06b7f061e8055d7e4046dafdb/'
    r'd388baee686640ddcb501ea53\.js"></script>'
)

matches = list(mailchimp_pattern.finditer(text))

if len(matches) > 1:
    first = True

    def keep_first(match):
        global first
        if first:
            first = False
            return match.group(0)
        return ''

    text = mailchimp_pattern.sub(keep_first, text)

    print(f"Removed {len(matches)-1} duplicate Mailchimp scripts.")


# --------------------------------------------------
# 5. Remove SECOND duplicate et_custom-css block
#    KEEP FIRST ONE
# --------------------------------------------------
custom_css_pattern = re.compile(
    r'<style\s+type="text/css"\s+class="et_custom-css">.*?</style>',
    re.DOTALL
)

blocks = list(custom_css_pattern.finditer(text))

if len(blocks) >= 2:
    second = blocks[1]

    text = (
        text[:second.start()]
        + text[second.end():]
    )

    print("Removed second et_custom-css block.")


# --------------------------------------------------
# SAVE
# --------------------------------------------------
file_path.write_text(text, encoding="utf-8")

print("Cleanup complete.")
print(f"Original backup is at: {backup}")