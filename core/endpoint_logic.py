import os
import json
import importlib
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, UploadFile, File
from core.database import engine
import sys
import random
# Templating rendszer (Jinja2)
templates = Jinja2Templates(directory="templates")

def generate_data():
    # 5 objektum létrehozása, mindegyik tartalmaz képet, nevet, leírást és értékelést
    items = []
    for i in range(1, 6):
        item = {
            "id": i,
            "image": f"/static/img/sample_image_{i}.jpg",
            "name": f"Item {i}",
            "description": f"This is a description for item {i}.",
            "rating": random.uniform(1, 100)
        }
        items.append(item)

    # Egy elem kiválasztása a legjobbnak
    best_item = max(items, key=lambda x: x['rating'])
    best_item["explanation"] = f"This is why item {best_item['id']} is considered the best."

    return {
        "items": items,
        "best_item_id": best_item['id'],
        "best_item_explanation": best_item['explanation']
    }

def handle_file_upload(file: UploadFile):
    # Ellenőrizzük, hogy a fájl PDF típusú-e
    print("Belépett")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Csak PDF fájlokat lehet feltölteni")

    # PDF fájl mentése a "documents" mappába
    save_path = os.path.join("documents", file.filename)
    with open(save_path, "wb") as buffer:
        buffer.write(file.file.read())

    return {"message": "Fájl sikeresen feltöltve", "filename": file.filename}


def load_all_avaliable_modules(request):
    modules = []
    addons_path = os.path.join(os.getcwd(), "addons")
    placeholder_img = "/static/img/placeholder.jpg"  # Helykitöltő kép, ha nincs logó

    for module_dir in os.listdir(addons_path):
        module_path = os.path.join(addons_path, module_dir)
        info_path = os.path.join(module_path, "module_info.json")
        css_path = f"/addons/{module_dir}/static/src/css/module.css"
        img_path = f"/addons/{module_dir}/static/src/img/logo.jpg"

        if os.path.exists(info_path):
            with open(info_path, 'r') as f:
                module_info = json.load(f)
                module_info['url'] = f"/modules/{module_dir}"  # Modul URL
                if os.path.exists(os.path.join(module_path, "static/src/css/module.css")):
                    module_info['css_path'] = css_path  # Modul-specifikus CSS
                else:
                    module_info['css_path'] = None  # Nincs modul-specifikus CSS

                # Ellenőrizzük, hogy van-e logó kép, ha nincs, használjunk helykitöltőt
                if os.path.exists(os.path.join(module_path, "static/src/img/logo.jpg")):
                    module_info['img_path'] = img_path
                else:
                    module_info['img_path'] = placeholder_img  # Helykitöltő kép

                # Ellenőrizzük, hogy a modul már hozzá van-e adva
                if module_info not in modules:
                    modules.append(module_info)

    # Modulok megjelenítése a kezdőoldalon
    return templates.TemplateResponse("home.html", {"request": request, "modules": modules})


def load_module(module_name, request):
    addons_path = os.path.join(os.getcwd(), "addons", module_name)
    info_path = os.path.join(addons_path, "module_info.json")
    template_dir = os.path.join(addons_path, "templates")
    template_path = os.path.join(template_dir, "admin_homepage.html")

    if not os.path.exists(info_path):
        raise HTTPException(status_code=404, detail="Module not found")

    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Module template not found")

    with open(info_path, 'r') as f:
        module_info = json.load(f)

    # Templating rendszer (Jinja2) - dinamikusan állítjuk be az adott modul templates mappáját
    templates = Jinja2Templates(directory=template_dir)

    # Modul oldalt rendereljük
    return templates.TemplateResponse("admin_homepage.html", {"request": request, "module": module_info})

def test_database_connection():
    try:
        # Ellenőrizzük az adatbázis kapcsolatot az engine használatával
        with engine.connect() as connection:
            print("Sikeresen csatlakoztunk az adatbázishoz!")
    except Exception as e:
        print(f"Nem sikerült csatlakozni az adatbázishoz: {e}")
        sys.exit(1)  # Kilépünk, ha az adatbázis kapcsolat sikertelen


if __name__ == "__main__":
    pass
