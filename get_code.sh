# 1. Start by removing the old file to ensure a clean slate
rm -f all_code.txt 

# 2. Find and concatenate files with headers
find . -type d \( -name "backend" -o -name "frontend" \) -exec find {} -name "*.py" -print0 \; | \
while IFS= read -r -d $'\0' file; do
    echo "# ========== $file ==========" >> all_code.txt
    cat "$file" >> all_code.txt
    echo "" >> all_code.txt
done
