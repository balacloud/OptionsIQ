
import os, shutil
src = '/root/options-edu-panel.html'
dst = '/home/user/options-edu-panel.html'
shutil.copy2(src, dst)
print("Copied to", dst, os.path.exists(dst))
