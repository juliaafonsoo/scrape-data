#!/usr/bin/env python3
import os
import shutil

def rename_folders():
    base_path = "/Users/juliaafonso/code/scrape-data/anexos-email"
    
    if not os.path.exists(base_path):
        print(f"Pasta não encontrada: {base_path}")
        return
    
    # Lista todas as pastas no diretório
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f)) and f != ".DS_Store"]
    
    print(f"Encontradas {len(folders)} pastas para processar...")
    print()
    
    renamed_count = 0
    skipped_count = 0
    
    for folder_name in folders:
        original_path = os.path.join(base_path, folder_name)
        
        # Aplica a regra: pega tudo depois do "<"
        if "<" in folder_name:
            # Encontra a posição do "<" e pega tudo depois dele
            new_name = folder_name.split("<", 1)[1]  # split em no máximo 2 partes
            new_path = os.path.join(base_path, new_name)
            
            print(f"Renomeando:")
            print(f"  De: {folder_name}")
            print(f"  Para: {new_name}")
            
            try:
                # Verifica se já existe uma pasta com o novo nome
                if os.path.exists(new_path):
                    print(f"  ⚠️  AVISO: Pasta '{new_name}' já existe! Pulando...")
                    skipped_count += 1
                else:
                    os.rename(original_path, new_path)
                    print(f"  ✅ Renomeado com sucesso!")
                    renamed_count += 1
            except Exception as e:
                print(f"  ❌ Erro ao renomear: {e}")
                skipped_count += 1
        else:
            print(f"Mantendo nome original (sem '<'): {folder_name}")
            skipped_count += 1
        
        print()
    
    print("=" * 50)
    print(f"Resumo:")
    print(f"  Pastas renomeadas: {renamed_count}")
    print(f"  Pastas mantidas/puladas: {skipped_count}")
    print(f"  Total processadas: {len(folders)}")

if __name__ == "__main__":
    print("Script para renomear pastas")
    print("Regra: Remove tudo antes de '<' (incluindo o '<') do nome da pasta")
    print()
    
    # Pergunta confirmação antes de executar
    response = input("Deseja continuar com a renomeação? (s/N): ").lower().strip()
    
    if response in ['s', 'sim', 'y', 'yes']:
        rename_folders()
    else:
        print("Operação cancelada.")
