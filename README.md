# PassPrint Website

Site web professionnel pour PassPrint, entreprise spécialisée dans l'imprimerie et la vente de fournitures de bureau.

## Fonctionnalités

- Boutique en ligne avec panier
- Personnalisation web-to-print
- Interface client
- Formulaire de devis
- Design responsive
- Optimisé pour SEO et performance

## Déploiement

### Local

Ouvrez `index.html` dans votre navigateur pour voir le site.

Pour un serveur local :
- Avec Python : `python -m http.server 8000`
- Avec Node.js : `npx http-server`

### En ligne

Le site est statique et peut être déployé sur :

- **GitHub Pages** : Poussez le code sur GitHub et activez Pages.
- **Netlify** : Glissez-déposez le dossier ou connectez un repo Git.
- **Vercel** : Importez depuis Git et déployez automatiquement.

Pour le paiement Stripe, configurez une clé API réelle et un backend pour traiter les paiements.

## Structure

- `index.html` : Page d'accueil
- `pages/` : Autres pages (services, shop, etc.)
- `css/style.css` : Styles personnalisés
- `js/script.js` : JavaScript pour interactions
- `images/` : Images et logo