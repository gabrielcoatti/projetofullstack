import re

# Ler o arquivo
with open('lista.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remover linhas com console.log e console.error
lines = content.split('\n')
cleaned_lines = []

for line in lines:
    # Pular linhas que contêm apenas console.log ou console.error
    if re.search(r'^\s*console\.(log|error)\([^)]*\);\s*$', line):
        continue
    cleaned_lines.append(line)

# Salvar o arquivo limpo
with open('lista.html', 'w', encoding='utf-8') as f:
    f.write('\n'.join(cleaned_lines))

print(f"✅ Console statements removidos! Total de linhas removidas: {len(lines) - len(cleaned_lines)}")
