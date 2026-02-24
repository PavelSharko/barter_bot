import os
import re

directories = ['handlers', 'services', 'scheduler']
pattern = re.compile(r'(?:message\.answer|message\.reply|bot\.send_message|safe_send_message|call\.answer)\(\s*(?:text=)?[fF]?["\'](.*?)["\']', re.DOTALL)
output_lines = []
counter = 1

for d in directories:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for text_literal in matches:
                        text_literal = text_literal.replace('\n', ' ').strip()
                        if text_literal:
                            output_lines.append(f"{counter} - [{path}] - {text_literal}")
                            counter += 1

with open('ALL_TEXT_MSGS.txt', 'w', encoding='utf-8') as out:
    out.write("\n\n".join(output_lines))
