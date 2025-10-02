// Service Worker pour PassPrint PWA
const CACHE_NAME = 'passprint-v1.0.0';
const STATIC_CACHE_URLS = [
    '/',
    '/index.html',
    '/dashboard.html',
    '/admin.html',
    '/css/style.css',
    '/js/script.js',
    '/images/logo.svg',
    '/manifest.json'
];

// Installation du Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker: Installation...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Mise en cache des fichiers statiques');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('Service Worker: Installation terminée');
                return self.skipWaiting();
            })
    );
});

// Activation du Service Worker
self.addEventListener('activate', event => {
    console.log('Service Worker: Activation...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Suppression ancien cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Activation terminée');
            return self.clients.claim();
        })
    );
});

// Interception des requêtes
self.addEventListener('fetch', event => {
    // Stratégie de cache pour les fichiers statiques
    if (event.request.url.includes('/css/') ||
        event.request.url.includes('/js/') ||
        event.request.url.includes('/images/') ||
        event.request.url.includes('/manifest.json')) {

        event.respondWith(
            caches.match(event.request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    return fetch(event.request)
                        .then(response => {
                            if (response.ok) {
                                const responseClone = response.clone();
                                caches.open(CACHE_NAME)
                                    .then(cache => {
                                        cache.put(event.request, responseClone);
                                    });
                            }
                            return response;
                        });
                })
        );
    }
    // Stratégie réseau d'abord pour l'API
    else if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    if (response.ok) {
                        return response;
                    }
                    return caches.match(event.request);
                })
                .catch(() => {
                    return caches.match(event.request);
                })
        );
    }
});

// Gestion des notifications push
self.addEventListener('push', event => {
    console.log('Service Worker: Notification push reçue');

    let notificationData = {
        title: 'PassPrint',
        body: 'Nouvelle notification',
        icon: '/images/logo.svg',
        badge: '/images/logo.svg',
        tag: 'passprint-notification',
        requireInteraction: false,
        actions: [
            {
                action: 'view',
                title: 'Voir'
            },
            {
                action: 'dismiss',
                title: 'Fermer'
            }
        ]
    };

    if (event.data) {
        try {
            const data = event.data.json();
            notificationData = { ...notificationData, ...data };
        } catch (e) {
            console.error('Erreur parsing notification data:', e);
        }
    }

    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData)
    );
});

// Clic sur notification
self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Clic sur notification');

    event.notification.close();

    if (event.action === 'view') {
        // Ouvrir l'application
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'dismiss') {
        // Notification fermée
        return;
    } else {
        // Clic sur la notification
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then(clientList => {
                if (clientList.length > 0) {
                    return clientList[0].focus();
                }
                return clients.openWindow('/');
            })
        );
    }
});

// Synchronisation en arrière-plan
self.addEventListener('sync', event => {
    console.log('Service Worker: Sync event', event.tag);

    if (event.tag === 'background-sync') {
        event.waitUntil(
            // Synchroniser les données en arrière-plan
            syncData()
        );
    }
});

// Fonction de synchronisation
async function syncData() {
    try {
        // Synchroniser le panier
        const cartData = await getStoredCart();
        if (cartData && cartData.items.length > 0) {
            await fetch('/api/cart/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(cartData)
            });
        }

        // Synchroniser les notifications
        await checkForUpdates();

    } catch (error) {
        console.error('Erreur synchronisation:', error);
    }
}

// Récupérer le panier stocké
async function getStoredCart() {
    try {
        const cache = await caches.open('passprint-cart');
        const response = await cache.match('/cart');

        if (response) {
            return await response.json();
        }

        // Fallback vers localStorage via message
        const clients = await self.clients.matchAll();
        if (clients.length > 0) {
            const client = clients[0];
            return await client.postMessage({ action: 'get-cart' });
        }

    } catch (error) {
        console.error('Erreur récupération panier:', error);
    }

    return null;
}

// Vérifier les mises à jour
async function checkForUpdates() {
    try {
        const response = await fetch('/api/updates/check');
        if (response.ok) {
            const updates = await response.json();

            if (updates.has_updates) {
                await self.registration.showNotification(
                    'PassPrint - Mises à jour',
                    {
                        body: 'Nouveaux produits ou promotions disponibles',
                        icon: '/images/logo.svg',
                        tag: 'updates',
                        requireInteraction: true
                    }
                );
            }
        }
    } catch (error) {
        console.error('Erreur vérification mises à jour:', error);
    }
}

// Gestion des messages
self.addEventListener('message', event => {
    console.log('Service Worker: Message reçu', event.data);

    if (event.data && event.data.action === 'skip-waiting') {
        self.skipWaiting();
    }
});

// Erreur non gérée
self.addEventListener('error', event => {
    console.error('Service Worker: Erreur non gérée', event.error);
});

// Promesse non gérée
self.addEventListener('unhandledrejection', event => {
    console.error('Service Worker: Promesse non gérée', event.reason);
    event.preventDefault();
});