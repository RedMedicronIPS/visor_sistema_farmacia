import inspect
import docx2pdf

print("module:", docx2pdf.__file__)
print("source lines:\n")
source = inspect.getsource(docx2pdf)
for line in source.splitlines()[:120]:
    print(line)
