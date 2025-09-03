#!/usr/bin/env python3
import os

def preview_rename():
    base_path = "/Users/juliaafonso/code/scrape-data/anexos-email"
    
    if not os.path.exists(base_path):
        print(f"Pasta não encontrada: {base_path}")
        return
    
    # Lista todas as pastas no diretório
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f)) and f != ".DS_Store"]
    
    print(f"PREVIEW: {len(folders)} pastas encontradas")
    print("=" * 80)
    
    will_rename = []
    will_keep = []
    
    for folder_name in folders:
        if "<" in folder_name:
            new_name = folder_name.split("<", 1)[1]
            will_rename.append((folder_name, new_name))
            print(f"RENOMEAR:")
            print(f"  📁 {folder_name}")
            print(f"  ➡️  {new_name}")
            print()
        else:
            will_keep.append(folder_name)
            print(f"MANTER: {folder_name}")
            print()
    
    print("=" * 80)
    print(f"Resumo do Preview:")
    print(f"  Serão renomeadas: {len(will_rename)} pastas")
    print(f"  Serão mantidas: {len(will_keep)} pastas")
    
    return len(will_rename) > 0

if __name__ == "__main__":
    print("PREVIEW - Renomeação de pastas")
    print("Regra: Remove tudo antes de '<' (incluindo o '<') do nome da pasta")
    print()
    
    has_changes = preview_rename()
    
    if has_changes:
        print("\n" + "=" * 80)
        response = input("Deseja executar a renomeação? (s/N): ").lower().strip()
        
        if response in ['s', 'sim', 'y', 'yes']:
            print("\nExecutando renomeação...")
            exec(open('/Users/juliaafonso/code/scrape-data/rename_folders.py').read())
        else:
            print("Operação cancelada.")
    else:
        print("Nenhuma pasta precisa ser renomeada.")
