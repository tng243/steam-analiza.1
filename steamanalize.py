import customtkinter
import api
import parser
import pandas as pd
from PIL import Image
import requests
from dotenv import load_dotenv
import os
import urllib.parse
import threading

# Ustawienie ścieżki pod exe
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        if not os.path.exists("images"):
            os.makedirs("images")
        self.title("Steam Inventory Analyzer")
        # Fullscreen i bindowanie ESC
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda event: self.destroy())

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Ramka startowa
        self.start_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.start_frame.grid(row=0, column=0)

        self.button = customtkinter.CTkButton(self.start_frame, text="Enter", 
                                            command=self.button_callback, 
                                            font=("Arial", 16, "bold"), width=200, height=40)
        self.button.grid(row=0, column=0, padx=20, pady=20)

        self.checkbox_1 = customtkinter.CTkCheckBox(self.start_frame, text="I accept the Terms of Use (link)")
        self.checkbox_1.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        self.checkbox_2 = customtkinter.CTkCheckBox(self.start_frame, text="This app is not affiliated with VALVE Corp.")
        self.checkbox_2.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        
        self.entry = customtkinter.CTkEntry(self.start_frame, placeholder_text="ENTER STEAM URL or ID", width=350, height=40)
        self.entry.bind("<Return>", self.show_inventory)
        
        self.label_error = customtkinter.CTkLabel(self.start_frame, text="YOU MUST ACCEPT TERMS!", 
                                                text_color="#ff6b6b", font=("Arial", 14, "bold"))

    def button_callback(self):
        if self.checkbox_1.get() == 1 and self.checkbox_2.get() == 1:
            self.button.grid_forget()
            self.checkbox_1.grid_forget()
            self.checkbox_2.grid_forget()
            self.label_error.grid_forget()
            self.entry.grid(row=0, column=0, padx=20, pady=20)
            self.entry.focus()
        else:
            self.label_error.grid(row=3, column=0, padx=20, pady=10)

    def show_inventory(self, event):
        self.start_frame.grid_forget()
        
        # Info o ładowaniu danych
        self.loading_label = customtkinter.CTkLabel(self, text="Fetching inventory and item data...\nPlease wait, this may take a moment.", font=("Arial", 20))
        self.loading_label.grid(row=0, column=0, sticky="nsew")
        
        # Wątek żeby nie mroziło okna
        threading.Thread(target=self.fetch_data_thread, daemon=True).start()

    def fetch_data_thread(self):
        link = self.entry.get()
        steam_id = api.get_steam_id(link)
        raw_data = api.ekwipunek(steam_id)

        if raw_data:
            parser.aktualizuj_ekwipunek_csv(steam_id, raw_data)
        
        self.after(0, lambda: self.display_grid(steam_id))

    def display_grid(self, steam_id):
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()

        self.scrollable_frame = customtkinter.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew") 
        
        for i in range(4):
            self.scrollable_frame.grid_columnconfigure(i, weight=1, uniform="col")

        csv_path = f"steamid_{steam_id}.csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            for i, item in df.iterrows():
                row, col = i // 4, i % 4
                
                # Renderowanie miniatury skina
                img_path = f"images/{item['asset_id']}.png"
                img = Image.open(img_path) if os.path.exists(img_path) else Image.new('RGB', (64, 64), color='gray')
                ctk_image = customtkinter.CTkImage(img.resize((64, 64)), size=(64, 64))

                btn = customtkinter.CTkButton(self.scrollable_frame, image=ctk_image,
                                            text=f"{item['bron']}\n{item['nazwa_skina']}",
                                            compound='top', command=lambda p=item: self.open_item_window(p))
                btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        else:
            customtkinter.CTkLabel(self.scrollable_frame, text="Inventory not found.").grid(row=0, column=0)

    def open_item_window(self, item):
        self.scrollable_frame.grid_forget()
        
        # Ramka detali przedmiotu
        self.detail_frame = customtkinter.CTkFrame(self)
        self.detail_frame.grid(row=0, column=0, sticky="nsew")
        
        self.detail_frame.grid_columnconfigure(0, weight=1)
        self.detail_frame.grid_rowconfigure(3, weight=1) 

        # Duży obrazek skina
        try:
            img_path = f"images/{item['asset_id']}.png"
            img = Image.open(img_path).resize((256, 256))
            ctk_image = customtkinter.CTkImage(img, size=(256, 256))
            label_img = customtkinter.CTkLabel(self.detail_frame, image=ctk_image, text="")
            label_img.grid(row=0, column=0, padx=20, pady=20)
        except:
            customtkinter.CTkLabel(self.detail_frame, text="Image missing").grid(row=0, column=0)

        label_name = customtkinter.CTkLabel(self.detail_frame, 
                                            text=f"{item['bron']} | {item['nazwa_skina']}",
                                            font=("Arial", 22, "bold"))
        label_name.grid(row=1, column=0, padx=20, pady=5)

        # Obsługa API i ceny
        market_name = f"{item['bron']} | {item['nazwa_skina']} ({item['stan']})"
        api_key = os.getenv('STEAMAPIS_KEY')
        api_url = f"https://api.steamapis.com/market/item/730/{urllib.parse.quote(market_name)}?api_key={api_key}"
        
        self.price_container = customtkinter.CTkLabel(self.detail_frame, text="Loading price...", font=("Arial", 18))
        self.price_container.grid(row=2, column=0, pady=10)
        
        try:
            response = requests.get(api_url, timeout=5)
            res_data = response.json()
            
            if 'histogram' in res_data:
                price = res_data['histogram']['sell_order_summary']['price']
                self.price_container.configure(text=f"Current Price: ${price}")
                
                # Wykres historii cen
                import matplotlib.pyplot as plt
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

                fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
                fig.patch.set_facecolor('#2b2b2b')
                ax.set_facecolor('#2b2b2b')
                ax.tick_params(colors='white')
                
                dates = []
                prices = []
                if 'median_avg_prices_15days' in res_data:
                    for entry in res_data['median_avg_prices_15days']:
                        dates.append(entry[0][:6]) 
                        prices.append(entry[1])

                if dates and prices:
                    ax.plot(dates, prices, color='#1f6aa5', marker='o', linewidth=2)
                    plt.xticks(rotation=45, ha='right', fontsize=8)
                    ax.set_title("Price History (Last 15 Days)", color='white')
                    fig.tight_layout()
                    
                    canvas = FigureCanvasTkAgg(fig, master=self.detail_frame)
                    canvas.draw()
                    canvas.get_tk_widget().grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
                else:
                    customtkinter.CTkLabel(self.detail_frame, text="No historical data found").grid(row=3, column=0)
            else:
                self.price_container.configure(text="Price: N/A (API issue)", text_color="orange")

        except Exception as e:
            self.price_container.configure(text=f"API Error: Check Connection", text_color="#ff6b6b")

        btn_back = customtkinter.CTkButton(self.detail_frame, text="Back", command=self.cofnij)
        btn_back.grid(row=4, column=0, padx=20, pady=20)

    def cofnij(self):
        # Powrót do ekwipunku
        if hasattr(self, 'detail_frame'):
            self.detail_frame.destroy()
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    app = App()
    app.mainloop()