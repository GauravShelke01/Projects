# 🔧 "pip is not recognized" Error — Complete Fix Guide (Windows)

```
pip : The term 'pip' is not recognized as the name of a cmdlet, function,
script file, or operable program...
```

Ye error ka matlab: **pip install to hai, bas Windows ko uska raasta (PATH) nahi pata.**
Niche diye tarike upar se niche try karo — pehla hi 90% cases me kaam kar jaata hai.

---

## ✅ FIX 1 — `py -m pip` use karo (sabse aasan, 99% kaam karta hai)

`py` naam ka "Python Launcher" Windows me `C:\Windows\` folder me install hota hai,
jo hamesha PATH me hota hai. Isliye ye tab bhi chalta hai jab `pip` fail ho jaye.

PowerShell / CMD me ye likho:

```powershell
py -m pip install flask pandas jinja2 schedule
```

Aur project run karne ke liye:

```powershell
py app.py
```

> Bas itna hi. Har jagah `pip` ki jagah `py -m pip` aur `python` ki jagah `py` likh do.

---

## ✅ FIX 2 — `python -m pip` try karo

```powershell
python -m pip install flask pandas jinja2 schedule
```

Agar `python` likhne par **Microsoft Store khul jaye**, to ye Windows ka fake stub hai.
Fix: `Settings → Apps → Advanced app settings → App execution aliases` →
`python.exe` aur `python3.exe` dono ko **OFF** kar do. Phir FIX 1 use karo.

---

## ✅ FIX 3 — Pehle check karo Python install hai bhi ya nahi

PowerShell me ek-ek karke chalao:

```powershell
py --version
python --version
where.exe python
```

| Output | Matlab | Kya kare |
|--------|--------|----------|
| `Python 3.12.x` aa gaya | Python hai ✔ | **FIX 1** use karo |
| Kuch bhi nahi / error | Python hi nahi hai ✘ | **FIX 5** (fresh install) |
| Microsoft Store khul gaya | Fake stub hai | **FIX 2** ka note padho |

---

## ✅ FIX 4 — PATH me manually add karo (permanent solution)

### Step A — Python kahan install hai wo pata karo
```powershell
py -c "import sys; print(sys.executable)"
```
Output kuch aisa aayega:
```
C:\Users\<YourName>\AppData\Local\Programs\Python\Python312\python.exe
```

Isme se **2 folder** yaad rakho:
```
C:\Users\<YourName>\AppData\Local\Programs\Python\Python312\
C:\Users\<YourName>\AppData\Local\Programs\Python\Python312\Scripts\
```
(dusra wala `Scripts` folder hi pip ka ghar hai)

### Step B — Environment Variables me daalo
1. Windows search me likho → **"Environment Variables"**
2. **"Edit the system environment variables"** kholo
3. Niche **"Environment Variables…"** button dabao
4. Upar wale box (**User variables**) me **`Path`** select karo → **Edit**
5. **New** dabake dono folders ek-ek karke paste karo (Step A wale)
6. **OK → OK → OK**
7. ⚠️ **PowerShell/CMD band karke dobara kholo** (warna purana PATH hi rahega)
8. Test: `pip --version`

---

## ✅ FIX 5 — Python dobara install karo (sabse safe)

1. Jao 👉 **https://www.python.org/downloads/**
2. Bada peela button **"Download Python 3.x"** dabao
3. Installer chalao aur **sabse niche 2 checkbox dekho:**

```
[x]  Use admin privileges when installing py.exe
[x]  Add python.exe to PATH        <-- YE WALA ZAROOR TICK KARO
```

4. **"Install Now"** dabao
5. Install hone ke baad **computer restart** karo
6. Test karo:
```powershell
python --version
pip --version
```

---

## ✅ FIX 6 — Ek click me sab kuch (shortcut)

Maine project folder me **`START_PROJECT.bat`** file bana di hai.

👉 Bas us file par **double-click** karo.

Wo khud:
- Python dhoondegi (`py` / `python` / `python3` me se jo mile)
- Saare packages install karegi
- App start karegi
- Browser apne aap khol degi

Agar Python hi na mile to wo poore install steps screen par dikha degi.

---

## 📌 Bonus — Virtual Environment (optional, but professional)

Viva me extra marks ke liye 😎

```powershell
py -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Agar `activate` par error aaye — *"running scripts is disabled on this system"*:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
`Y` dabao, phir dobara `.\venv\Scripts\activate` chalao.

Band karne ke liye: `deactivate`

---

## 🎯 Quick Summary — bas ye 2 command yaad rakho

| Purana (error dega) | Naya (chalega) |
|---------------------|----------------|
| `pip install flask` | `py -m pip install flask` |
| `python app.py` | `py app.py` |
