(() => {
    const storageKey = "snapcase-wishlist";
    const page = document.getElementById("wishlist-products");
    const emptyState = document.getElementById("wishlist-empty");
    const status = document.getElementById("wishlist-status");

    function readWishlist() {
        const storedItems = localStorage.getItem(storageKey);
        if (!storedItems) return [];

        const items = JSON.parse(storedItems);
        if (!Array.isArray(items)) {
            throw new Error("Your wishlist data is invalid. Please clear it and try again.");
        }

        return items.filter((item) =>
            item
            && /^\d+$/.test(String(item.id))
            && typeof item.name === "string"
            && typeof item.price === "string"
            && typeof item.image === "string"
            && typeof item.brand === "string"
        );
    }

    function updateControls(items) {
        const savedIds = new Set(items.map((item) => String(item.id)));
        document.querySelectorAll(".wishlist-count").forEach((count) => {
            count.textContent = String(items.length);
        });
        document.querySelectorAll(".wishlist-toggle").forEach((button) => {
            const saved = savedIds.has(button.dataset.productId);
            button.setAttribute("aria-pressed", String(saved));
            button.textContent = saved ? "♥" : "♡";
            button.setAttribute(
                "aria-label",
                `${saved ? "Remove" : "Add"} ${button.dataset.productName} ${saved ? "from" : "to"} wishlist`
            );
        });
    }

    function makeWishlistCard(item) {
        const article = document.createElement("article");
        article.className = "product-card";

        const productUrl = `/products/${item.id}/`;
        const imageLink = document.createElement("a");
        imageLink.className = "product-image product-detail-link";
        imageLink.href = productUrl;
        imageLink.setAttribute("aria-label", `View details for ${item.name}`);

        const image = document.createElement("img");
        const imageUrl = new URL(item.image, window.location.origin);
        image.src = imageUrl.origin === window.location.origin
            && (imageUrl.pathname.startsWith("/static/") || imageUrl.pathname.startsWith("/media/"))
            ? imageUrl.href
            : "/static/images/plain-clear.jpg";
        image.alt = item.name;
        imageLink.append(image);
        article.append(imageLink);

        const info = document.createElement("div");
        info.className = "product-info";

        const compatibility = document.createElement("p");
        compatibility.className = "compatibility";
        compatibility.textContent = item.brand;
        info.append(compatibility);

        const heading = document.createElement("h3");
        const productLink = document.createElement("a");
        productLink.className = "product-name-link";
        productLink.href = productUrl;
        productLink.textContent = item.name;
        heading.append(productLink);
        info.append(heading);

        const price = document.createElement("p");
        price.className = "wishlist-price";
        price.textContent = `₹${item.price}`;
        info.append(price);

        const removeButton = document.createElement("button");
        removeButton.className = "wishlist-remove";
        removeButton.type = "button";
        removeButton.dataset.productId = String(item.id);
        removeButton.textContent = "Remove from wishlist";
        info.append(removeButton);
        article.append(info);
        return article;
    }

    function renderPage(items) {
        if (!page) return;
        page.replaceChildren(...items.map(makeWishlistCard));
        emptyState.hidden = items.length > 0;
    }

    function refresh() {
        const items = readWishlist();
        updateControls(items);
        renderPage(items);
        if (status) {
            status.hidden = true;
            status.textContent = "";
        }
    }

    function save(items) {
        localStorage.setItem(storageKey, JSON.stringify(items));
        refresh();
    }

    document.addEventListener("click", (event) => {
        const toggle = event.target.closest(".wishlist-toggle");
        const remove = event.target.closest(".wishlist-remove");
        if (!toggle && !remove) return;

        try {
            const items = readWishlist();
            const productId = (toggle || remove).dataset.productId;
            const existingIndex = items.findIndex((item) => String(item.id) === productId);
            if (existingIndex >= 0) {
                items.splice(existingIndex, 1);
            } else if (toggle) {
                items.push({
                    id: productId,
                    name: toggle.dataset.productName,
                    price: toggle.dataset.productPrice,
                    image: toggle.dataset.productImage,
                    brand: toggle.dataset.productBrand
                });
            }
            save(items);
        } catch (error) {
            window.console.error("Could not update your wishlist:", error);
            if (status) {
                status.textContent = error.message;
                status.hidden = false;
            } else {
                window.alert(error.message || "Could not update your wishlist.");
            }
        }
    });

    window.addEventListener("storage", (event) => {
        if (event.key === storageKey) {
            try {
                refresh();
            } catch (error) {
                window.console.error("Could not refresh your wishlist:", error);
            }
        }
    });

    try {
        refresh();
    } catch (error) {
        window.console.error("Could not load your wishlist:", error);
        if (status) {
            status.textContent = error.message;
            status.hidden = false;
        }
    }
})();
