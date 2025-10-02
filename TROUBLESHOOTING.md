# 🚨 Guide de Dépannage PassPrint

Si le site ne s'affiche pas correctement, suivez ces étapes :

## 🔍 **DIAGNOSTIC RAPIDE**

### **1. Vérifier le Serveur**
```bash
# Dans un terminal, tapez:
python server_simple.py
```

**Vous devriez voir :**
```
Serveur PassPrint demarre...
Site web: http://localhost:5000
Dashboard: http://localhost:5000/dashboard.html
==================================================
 * Running on http://127.0.0.1:5000/
```

### **2. Test de Base**
Ouvrez dans votre navigateur :
- **http://localhost:5000** (site principal)
- **http://127.0.0.1:5000** (même chose)

## 🛠️ **SOLUTIONS AUX PROBLÈMES COURANTS**

### **❌ "Site ne répond pas"**
**Solution :**
1. Fermez tous les terminaux
2. Double-cliquez sur `start_simple.bat`
3. Attendez que le serveur démarre
4. Ouvrez http://localhost:5000

### **❌ "Dashboard ne s'affiche pas"**
**Solution :**
1. Ouvrez http://localhost:5000/dashboard.html
2. Si ça ne marche pas, essayez http://localhost:5000/test-admin.html
3. Le dashboard devrait s'afficher avec des statistiques

### **❌ "Page blanche"**
**Solution :**
1. Appuyez sur F12 dans le navigateur
2. Vérifiez la console pour les erreurs
3. Actualisez la page (Ctrl+F5)

### **❌ "Images ne se chargent pas"**
**Solution :**
- Les images sont dans le dossier `images/`
- Vérifiez que le dossier existe
- Actualisez le cache du navigateur

## 🚀 **DÉMARRAGE GARANTI**

### **Option 1: Automatique (Recommandé)**
```bash
# Double-cliquez simplement sur:
start_simple.bat
```

### **Option 2: Manuel**
```bash
# Dans un terminal:
python server_simple.py
```

### **Option 3: Dashboard Spécifique**
```bash
# Double-cliquez sur:
open_dashboard.bat
```

## 🌐 **URLS DE TEST**

| Description | URL | Fonction |
|-------------|-----|----------|
| **Site Principal** | http://localhost:5000 | Page d'accueil |
| **Dashboard Complet** | http://localhost:5000/dashboard.html | Admin complet |
| **Dashboard Test** | http://localhost:5000/test-admin.html | Version simple |
| **Dashboard Original** | http://localhost:5000/admin.html | Version originale |

## 🔧 **RÉSOLUTION AVANCÉE**

### **Si rien ne marche :**

1. **Fermez tous les navigateurs**
2. **Fermez tous les terminaux**
3. **Redémarrez votre ordinateur**
4. **Double-cliquez sur `start_simple.bat`**
5. **Ouvrez http://localhost:5000**

### **Vérification des Ports :**
```bash
# Vérifiez si le port 5000 est libre:
netstat -an | find "5000"
```

### **Nettoyage Complet :**
```bash
# Fermez tous les processus Python:
taskkill /f /im python.exe
```

## 📞 **SUPPORT**

Si le problème persiste :

1. **Vérifiez que Python est installé :**
   ```bash
   python --version
   ```

2. **Vérifiez que Flask est installé :**
   ```bash
   python -c "import flask; print('Flask OK')"
   ```

3. **Démarrer en mode sans échec :**
   ```bash
   python test_flask.py
   ```

## ✅ **VÉRIFICATION FINALE**

Une fois le serveur démarré, vous devriez pouvoir :

- ✅ **Accéder au site :** http://localhost:5000
- ✅ **Voir le dashboard :** http://localhost:5000/dashboard.html
- ✅ **Naviguer entre les pages**
- ✅ **Voir les statistiques et graphiques**
- ✅ **Gérer les commandes et produits**

---

**🎯 Le site devrait maintenant fonctionner parfaitement!**