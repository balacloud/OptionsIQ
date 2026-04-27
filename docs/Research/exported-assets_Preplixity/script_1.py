
import os

html_content = open('/root/options-edu-panel.html').read() if os.path.exists('/root/options-edu-panel.html') else None

# write to home
with open(os.path.expanduser('~/options-edu-panel.html'), 'w') as f:
    f.write(html_content)
print("saved to", os.path.expanduser('~/options-edu-panel.html'))
