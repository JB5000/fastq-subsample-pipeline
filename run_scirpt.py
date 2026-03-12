import os
import shutil
import subprocess

# 1. Caminho base onde estão os teus ficheiros (Downloads)
BASE_DIR = "/home/jonyb/Downloads"

# 2. Pasta onde vai ficar todo o output
OUT_DIR = os.path.join(BASE_DIR, "subsamples_emobon")
CSV_OUT = os.path.join(OUT_DIR, "samplesheet.csv")

# Ficheiros originais que acabaste de descarregar
M1_R1 = os.path.join(BASE_DIR, "EMOBON_RFormosa_So_210805_micro_1_DBH_AAALOSDA_1_1_HMNJKDSX3.UDI236_clean.fastq.gz")
M1_R2 = os.path.join(BASE_DIR, "EMOBON_RFormosa_So_210805_micro_1_DBH_AAALOSDA_1_2_HMNJKDSX3.UDI236_clean.fastq.gz")
M2_R1 = os.path.join(BASE_DIR, "EMOBON_RFormosa_So_210805_micro_2_DBH_AAAMOSDA_4_1_HMNJKDSX3.UDI250_clean.fastq.gz")
M2_R2 = os.path.join(BASE_DIR, "EMOBON_RFormosa_So_210805_micro_2_DBH_AAAMOSDA_4_2_HMNJKDSX3.UDI250_clean.fastq.gz")

# Criar a pasta de output se ainda não existir
os.makedirs(OUT_DIR, exist_ok=True)

# Nomes para os ficheiros concatenados (A nossa amostra a 100%)
CONCAT_R1 = os.path.join(OUT_DIR, "EMOBON_Concat_100_R1.fastq.gz")
CONCAT_R2 = os.path.join(OUT_DIR, "EMOBON_Concat_100_R2.fastq.gz")

# Função segura para juntar os ficheiros .gz
def concatenar_ficheiros(ficheiro1, ficheiro2, output):
    with open(output, 'wb') as wfd:
        for f in [ficheiro1, ficheiro2]:
            with open(f, 'rb') as fd:
                shutil.copyfileobj(fd, wfd)

# --- INÍCIO DO PROCESSO ---

print("1. A concatenar ficheiros M1 e M2 (Isto vai demorar alguns minutos para 12GB)...")
concatenar_ficheiros(M1_R1, M2_R1, CONCAT_R1)
concatenar_ficheiros(M1_R2, M2_R2, CONCAT_R2)
print("Concatenação concluída!")

# Semente fixa para garantir que as reads do R1 e R2 batem sempre certo
SEED = 12345

print("2. A iniciar o subsampling e a gerar o samplesheet.csv...")
# Abrir o ficheiro CSV para escrita
with open(CSV_OUT, 'w') as csv_file:
    # Cabeçalho exigido pelo pipeline nf-core/mag
    csv_file.write("sample,run_accession,instrument_platform,fastq_1,fastq_2,fasta\n")

    # Ciclo para gerar as frações de 10% a 90%
    for percent in range(10, 100, 10):
        print(f" -> A processar a fração de {percent}%...")
        
        fraction = percent / 100.0
        sample_id = f"EMOBON_Sub_{percent}"
        out_r1 = os.path.join(OUT_DIR, f"{sample_id}_R1.fastq.gz")
        out_r2 = os.path.join(OUT_DIR, f"{sample_id}_R2.fastq.gz")
        
        # Comandos para extrair reads aleatórias e voltar a comprimir
        cmd_r1 = f"seqtk sample -s {SEED} {CONCAT_R1} {fraction} | gzip > {out_r1}"
        cmd_r2 = f"seqtk sample -s {SEED} {CONCAT_R2} {fraction} | gzip > {out_r2}"
        
        # Executar os comandos no sistema
        subprocess.run(cmd_r1, shell=True, check=True)
        subprocess.run(cmd_r2, shell=True, check=True)
        
        # Escrever a linha no CSV
        csv_file.write(f"{sample_id},0,ILLUMINA,{out_r1},{out_r2},\n")

    # Por fim, adicionar a amostra completa a 100% no CSV
    csv_file.write(f"EMOBON_Sub_100,0,ILLUMINA,{CONCAT_R1},{CONCAT_R2},\n")

print(f"\n✅ Tudo concluído! Os teus ficheiros e o CSV estão prontos na pasta: {OUT_DIR}")