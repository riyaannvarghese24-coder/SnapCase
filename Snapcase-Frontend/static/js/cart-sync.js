(() => {
    const updateKey = "snapcase-cart-updated";
    let latestRequest = 0;

    async function fetchCart() {
        const response = await fetch("/api/cart/");
        if (response.status === 401) {
            return { items: [], count: 0, total: 0 };
        }
        if (!response.ok) throw new Error("Could not load your cart.");
        return response.json();
    }

    function refresh(callback) {
        const requestId = ++latestRequest;
        fetchCart()
            .then((cart) => {
                if (requestId === latestRequest) callback(cart);
            })
            .catch((error) => window.console.error(error));
    }

    window.SnapCaseCart = {
        publish() {
            try {
                localStorage.setItem(updateKey, `${Date.now()}-${Math.random()}`);
            } catch (error) {
                window.console.error("Could not notify other tabs about the cart update:", error);
            }
            window.dispatchEvent(new Event(updateKey));
        },
        subscribe(callback) {
            const refreshCart = () => refresh(callback);
            window.addEventListener("focus", refreshCart);
            window.addEventListener("pageshow", refreshCart);
            window.addEventListener(updateKey, refreshCart);
            window.addEventListener("storage", (event) => {
                if (event.key === updateKey) refreshCart();
            });
            refreshCart();
        }
    };
})();
