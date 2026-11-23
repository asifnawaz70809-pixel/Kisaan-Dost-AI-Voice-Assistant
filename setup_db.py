import sqlite3

def init_100_crop_database():
    # Database file automatically ban jayegi agar mojood nahi hui
    conn = sqlite3.connect('kisaan_database.db')
    cursor = conn.cursor()
    
    # Table creation for 100 Crops & Diseases
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Crop_Diseases_100 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT,
            disease_name TEXT,
            urdu_treatment TEXT
        )
    ''')
    
    # Sample data insertion (Aap isme mazeed entries add kar sakte hain)
    sample_data = [
        ("Wheat", "Wheat___Yellow_rust", "1. Peli rust wali fasal ke mutasir patton ko foran kaat kar zameen mein daba dein.<br>2. Khet mein zyaada pani jama na hone dein.<br>3. Propiconazole fungicide ka spray karein.<br>4. Nitrogen khad ka istemaal kam karein.<br>5. Behtareen beej ka intekhab karein."),
        ("Potato", "Potato___Late_blight", "1. Mutasir paudhon ko foran alag kar dein.<br>2. Barish mein pani khara na hone dein.<br>3. Metalaxyl + Mancozeb spray karein.<br>4. Beemari wali zameen mein aalu na boyein.<br>5. Helpline 0800-17000 par rabta karein."),
        ("Tomato", "Tomato___Late_blight", "1. Kharab patton aur phal ko tor kar phenk dein.<br>2. Drip irrigation ka istemaal karein.<br>3. Copper-based fungicide spray karein.<br>4. Khet mein dhoop aur hawa ka intezam karein.<br>5. Resistant qismein kasht karein.")
    ]
    
    cursor.executemany("INSERT OR IGNORE INTO Crop_Diseases_100 (crop_name, disease_name, urdu_treatment) VALUES (?, ?, ?)", sample_data)
    conn.commit()
    conn.close()
    print("✅ Database aur Table kamyabi se ban gayi hai!")

if __name__ == "__main__":
    init_100_crop_database()