import os

def replace_in_files(root_dir, search_text, replace_text):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(('.py', '.html', '.css', '.js', '.txt', '.rst', '.yml', '.yaml', '.po', '.pot', '.cfg')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if search_text in content:
                        new_content = content.replace(search_text, replace_text)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated: {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    # Case-sensitive replacements
    replace_in_files('src/imanage', 'imanage', 'imanage')
    replace_in_files('src/imanage', 'Imanage', 'Imanage')
    replace_in_files('doc', 'imanage', 'imanage')
    replace_in_files('doc', 'Imanage', 'Imanage')
    replace_in_files('.', 'imanage', 'imanage')
    replace_in_files('.', 'Imanage', 'Imanage')
