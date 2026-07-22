import subprocess
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of every window & size of every window'
]).decode().strip()
print("Raw output:", repr(out))
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
print("Nums:", nums)
print("Count:", len(nums))
