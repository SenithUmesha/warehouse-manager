from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "cw2" / "t1"

replacements = [
    (
        re.compile(r'String\s+url\s*=\s*"jdbc:mysql://localhost:3306/wms";'),
        'String url = AppConfig.dbUrl();',
    ),
    (
        re.compile(r'String\s+uname\s*=\s*"root";'),
        'String uname = AppConfig.dbUser();',
    ),
    (
        re.compile(r'String\s+pass\s*=\s*"[^"]*";'),
        'String pass = AppConfig.dbPassword();',
    ),
    (
        re.compile(r'String\s+myemail\s*=\s*"[^"]*";'),
        'String myemail = AppConfig.smtpUser();',
    ),
    (
        re.compile(r'String\s+mypassword\s*=\s*"[^"]*";'),
        'String mypassword = AppConfig.smtpPassword();',
    ),
    (
        re.compile(r'ThreadLocalRandom\.current\(\)\.nextInt\(\);'),
        'ThreadLocalRandom.current().nextInt(100000, 1000000);',
    ),
    (
        re.compile(r'new javax\.swing\.ImageIcon\("D:\\\\Downloads\\\\male_user_50px\.png"\)'),
        'new javax.swing.ImageIcon(getClass().getResource("/cw2/t1/male_user_50px.png"))',
    ),
]

changed = []
for path in SOURCE.glob("*.java"):
    original = path.read_text(encoding="utf-8")
    updated = original
    for pattern, replacement in replacements:
        updated = pattern.sub(replacement, updated)

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        changed.append(path.relative_to(ROOT).as_posix())

print("Sanitized:", ", ".join(changed) if changed else "no files")
