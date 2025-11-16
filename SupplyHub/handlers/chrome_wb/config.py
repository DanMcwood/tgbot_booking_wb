import logging
import random
import hashlib
import asyncio

def generate_canvas_hash(seed: int) -> int:
    """Генерация уникального хэша на основе входного значения."""
    random.seed(seed)
    data = "".join([chr(random.randint(0, 255)) for _ in range(100)])
    return int(hashlib.md5(data.encode()).hexdigest(), 16) % (10**10)

async def configure_page_for_stealth(page):
    """Расширенная маскировка автоматизации для прохождения тестов."""
    canvas_hashes = [generate_canvas_hash(i) for i in range(1, 6)]
    canvas_hashes_js = ", ".join([str(h) for h in canvas_hashes])
    await page.add_init_script("""

        // Маскировка navigator.languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ru-RU', 'ru']
        });

        // Маскировка navigator.userAgent
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36'
        });

        // Маскировка navigator.vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.'
        });

        // Маскировка Permissions API
        const originalPermissionsQuery = navigator.permissions.query;
        navigator.permissions.query = (params) => {
            if (params.name === 'notifications') {
                return Promise.resolve({ state: 'granted' });
            }
            return originalPermissionsQuery(params);
        };

        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(x, y, width, height) {
            console.log('getImageData вызван');
            return {
                data: new Uint8ClampedArray([120, 85, 50, 0]) // Ваш прозрачный пиксель
            };
        };
                               
        // Маскировка FontFaceSet API
        const originalFonts = document.fonts;
        Object.defineProperty(document, 'fonts', {
            get: () => {
                return {
                    status: "loaded",
                    ready: Promise.resolve(true),
                    check: (text, options) => true,
                    load: async (font) => [],
                    addEventListener: originalFonts.addEventListener.bind(originalFonts),
                    removeEventListener: originalFonts.removeEventListener.bind(originalFonts),
                };
            }
        });
                               
        // Эмуляция WebDriver Advanced
        window.chrome = {
            runtime: {}
        };
        Object.defineProperty(navigator, 'connection', {
            get: () => ({ effectiveType: '4g' })
        });

        // Эмуляция свойств DevTools Protocol
        Object.defineProperty(window, 'chrome', {
            get: () => ({
                loadTimes: () => ({}),
                csi: () => ({ startE: Date.now() })
            })
        });

        // Маскировка размеров экрана
        Object.defineProperty(window, 'outerWidth', { get: () => 1280 });
        Object.defineProperty(window, 'outerHeight', { get: () => 720 });
        Object.defineProperty(screen, 'width', { get: () => 1280 });
        Object.defineProperty(screen, 'height', { get: () => 720 });
        Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 1.0000000149011612 });
    """)
    
    """Расширенная маскировка Canvas."""
    await page.add_init_script("""
        (function() {
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            const originalGetContext = HTMLCanvasElement.prototype.getContext;

            function generateRandomHash() {
                return Math.floor(Math.random() * 1000000000);
            }

            const canvasHashes = new WeakMap();

            HTMLCanvasElement.prototype.toDataURL = function(type, quality) {
                if (!canvasHashes.has(this)) {
                    canvasHashes.set(this, generateRandomHash());
                }
                if (type === "image/png" || !type) {
                    return `data:image/png;base64,hash${canvasHashes.get(this)}`;
                }
                return originalToDataURL.call(this, type, quality);
            };

            CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {
                const imageData = originalGetImageData.call(this, sx, sy, sw, sh);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] ^= 120;
                    imageData.data[i + 1] ^= 85;
                    imageData.data[i + 2] ^= 50;
                }
                return imageData;
            };

            HTMLCanvasElement.prototype.getContext = function(contextType, contextAttributes) {
                if (contextType === "2d") {
                    const context = originalGetContext.call(this, contextType, contextAttributes);
                    return context;
                }
                return originalGetContext.call(this, contextType, contextAttributes);
            };
        })();
    """)

"""Рандомные скроллы страницы"""
async def random_scroll(page, min_scrolls=1, max_scrolls=3, delay=(0.5, 1.5)):
    """
    Случайная прокрутка страницы для повышения скрытности.
    :param page: Объект страницы Playwright.
    :param min_scrolls: Минимальное количество прокруток.
    :param max_scrolls: Максимальное количество прокруток.
    :param delay: Диапазон задержки между прокрутками (в секундах).
    """
    num_scrolls = random.randint(min_scrolls, max_scrolls)
    for _ in range(num_scrolls):
        scroll_y = random.randint(200, 800)
        await page.mouse.wheel(0, scroll_y)
        await asyncio.sleep(random.uniform(*delay))