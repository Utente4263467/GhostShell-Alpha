#!/usr/bin/env python3

import subprocess
import sys
import time
import os
from PIL import Image
import io
import select

# ANSI colors per output migliore
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def clear_screen():
    os.system('clear')

def print_ascii_title():
    title = f"""
{BOLD}{BLUE}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ██╗     ██╗██╗   ██╗███████╗███████╗ ██████╗██████╗     ║
║     ██║     ██║██║   ██║██╔════╝██╔════╝██╔════╝██╔══██╗    ║
║     ██║     ██║██║   ██║█████╗  ███████╗██║     ██████╔╝    ║
║     ██║     ██║╚██╗ ██╔╝██╔══╝  ╚════██║██║     ██╔══██╗    ║
║     ███████╗██║ ╚████╔╝ ███████╗███████║╚██████╗██║  ██║    ║
║     ╚══════╝╚═╝  ╚═══╝  ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝    ║
║                                                              ║
║                    LIVE SCREEN CONTROLLER                    ║
║                         v1.0 - Termux                        ║
╚══════════════════════════════════════════════════════════════╝
{RESET}
"""
    print(title)

def print_menu():
    menu = f"""
{YELLOW}╔════════════════════════════════════════════════════════╗
║                   MENU PRINCIPALE                         ║
╠════════════════════════════════════════════════════════╣
║  {GREEN}[1]{YELLOW}  Live Screen (Streaming in tempo reale)          ║
║  {RED}[0]{YELLOW}  Esci                                         ║
╚════════════════════════════════════════════════════════╝{RESET}
"""
    print(menu)

def check_adb():
    """Verifica se ADB è installato"""
    result = subprocess.run(['which', 'adb'], capture_output=True)
    if result.returncode != 0:
        print(f"{RED}❌ ADB non trovato! Installa con: pkg install android-tools{RESET}")
        return False
    return True

def wait_for_device():
    """Aspetta che il secondo telefono venga collegato"""
    print(f"\n{BLUE}📱 Collega il SECONDO telefono via USB (con USB Debugging attivo){RESET}")
    print(f"{YELLOW}⏳ In attesa di connessione... (premi Ctrl+C per annullare){RESET}")
    
    while True:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        
        devices = []
        for line in lines:
            if 'device' in line and 'offline' not in line:
                device_id = line.split('\t')[0]
                if device_id:
                    devices.append(device_id)
        
        if devices:
            print(f"{GREEN}✅ Telefono collegato: {devices[0]}{RESET}")
            return devices[0]
        
        time.sleep(2)
        print(".", end="", flush=True)

def select_fps():
    """Menu per selezionare i fotogrammi per secondo"""
    print(f"\n{BLUE}╔════════════════════════════════════════╗")
    print(f"║      SELEZIONA FOTGRAMMI AL SECONDO     ║")
    print(f"╠════════════════════════════════════════╣")
    print(f"║  {GREEN}[1]{BLUE}  15 FPS (Bassa qualità, più stabile)  ║")
    print(f"║  {GREEN}[2]{BLUE}  20 FPS (Qualità media)               ║")
    print(f"║  {GREEN}[3]{BLUE}  30 FPS (Alta qualità, più pesante)   ║")
    print(f"║  {GREEN}[4]{BLUE}  60 FPS (Massima qualità - sperimentale)║")
    print(f"╚════════════════════════════════════════╝{RESET}")
    
    while True:
        choice = input(f"{YELLOW}👉 Scegli [1-4]: {RESET}").strip()
        fps_map = {'1': 15, '2': 20, '3': 30, '4': 60}
        if choice in fps_map:
            return fps_map[choice]
        print(f"{RED}❌ Scelta non valida{RESET}")

def live_screen_stream(device_id, fps):
    """Avvia lo streaming live screen con i fotogrammi selezionati"""
    delay = 1.0 / fps
    
    print(f"\n{GREEN}🎬 Live Screen avviato! ({fps} FPS - {delay*1000:.0f}ms per frame){RESET}")
    print(f"{YELLOW}📺 Lo streaming apparirà in una nuova finestra...{RESET}")
    print(f"{RED}⚠️  Premi Ctrl+C per fermare lo streaming{RESET}\n")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        # Comando per screenshot continuo
        cmd = ['adb', '-s', device_id, 'exec-out', 'screencap', '-p']
        
        while True:
            frame_start = time.time()
            
            # Cattura screenshot
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0 and len(result.stdout) > 0:
                try:
                    # Converti in immagine
                    img = Image.open(io.BytesIO(result.stdout))
                    
                    # Ridimensiona per Termux (opzionale)
                    max_size = (800, 1200)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Salva temporaneamente e mostra
                    temp_path = f"/sdcard/live_frame_{frame_count}.png"
                    img.save(temp_path)
                    
                    # Mostra in Termux (usa il visualizzatore di default)
                    subprocess.run(['termux-open', temp_path], capture_output=True)
                    
                    # Rimuovi vecchi file (mantieni solo ultimi 5)
                    if frame_count > 5:
                        old_path = f"/sdcard/live_frame_{frame_count-5}.png"
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    frame_count += 1
                    
                    # Stats ogni 30 frame
                    if frame_count % 30 == 0:
                        elapsed = time.time() - start_time
                        actual_fps = frame_count / elapsed
                        print(f"{BLUE}📊 Statistiche: {actual_fps:.1f} FPS reali | Frame: {frame_count}{RESET}")
                    
                except Exception as e:
                    print(f"{RED}❌ Errore elaborazione immagine: {e}{RESET}")
            
            # Controlla il tempo per mantenere l'FPS richiesto
            frame_time = time.time() - frame_start
            sleep_time = max(0, delay - frame_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⏹️  Streaming interrotto{RESET}")
        print(f"{GREEN}📊 Totale frame catturati: {frame_count}{RESET}")
        
        # Pulisci file temporanei
        print(f"{YELLOW}🧹 Pulizia file temporanei...{RESET}")
        for i in range(frame_count - 10, frame_count + 1):
            temp_path = f"/sdcard/live_frame_{i}.png"
            if os.path.exists(temp_path):
                os.remove(temp_path)

def main():
    clear_screen()
    print_ascii_title()
    
    # Verifica ADB
    if not check_adb():
        sys.exit(1)
    
    while True:
        print_menu()
        choice = input(f"{YELLOW}👉 Scegli opzione: {RESET}").strip()
        
        if choice == '1':
            clear_screen()
            print_ascii_title()
            
            # Aspetta secondo telefono
            device_id = wait_for_device()
            
            # Seleziona FPS
            fps = select_fps()
            
            clear_screen()
            print_ascii_title()
            
            # Avvia live screen
            print(f"{GREEN}🚀 Avvio Live Screen in corso...{RESET}")
            print(f"{BLUE}📱 Dispositivo: {device_id}{RESET}")
            print(f"{BLUE}🎬 Fotogrammi/sec: {fps}{RESET}")
            time.sleep(2)
            
            live_screen_stream(device_id, fps)
            
            input(f"\n{GREEN}Premi Enter per tornare al menu{RESET}")
            clear_screen()
            print_ascii_title()
            
        elif choice == '0':
            print(f"{GREEN}👋 Arrivederci!{RESET}")
            sys.exit(0)
        else:
            print(f"{RED}❌ Opzione non valida{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠️  Programma terminato{RESET}")
        sys.exit(0)