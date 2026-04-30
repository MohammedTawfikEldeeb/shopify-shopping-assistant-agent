"""Utilities for processing product data for vector embeddings."""

import re
from html.parser import HTMLParser
from typing import Any

from loguru import logger as default_logger


class HTMLToTextParser(HTMLParser):
    """Parse HTML to clean text, preserving structure."""

    def __init__(self):
        super().__init__()
        self.text_parts: list[str] = []
        self.skip_content = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("meta", "script", "style"):
            self.skip_content = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("meta", "script", "style"):
            self.skip_content = False
        elif tag in ("p", "div", "li", "br"):
            if self.text_parts and self.text_parts[-1] != " ":
                self.text_parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.skip_content:
            text = data.strip()
            if text:
                self.text_parts.append(text)

    def get_text(self) -> str:
        """Return cleaned text."""
        text = " ".join(self.text_parts)
        # Clean up multiple spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text


def clean_html(html_text: str | None) -> str | None:
    """Convert HTML to clean plain text."""
    if not html_text:
        return None

    try:
        parser = HTMLToTextParser()
        parser.feed(html_text)
        clean_text = parser.get_text()
        return clean_text if clean_text else None
    except Exception as e:
        default_logger.warning(f"Failed to parse HTML: {e}")
        return None


def extract_material_info(description: str) -> str | None:
    """Extract material composition from description text."""
    if not description:
        return None

    # Match patterns like "100% cotton" or "Polyester blend"
    pattern = r"([\d\s]*%?\s*[a-z\s,&-]*(?:cotton|polyester|silk|wool|linen|nylon|spandex|elastane|lycra|bamboo|hemp|leather|suede|mesh|fleece|denim|rayon|viscose|acrylic|blend)[\w\s,&]*)"
    matches = re.findall(pattern, description, re.IGNORECASE)

    if matches:
        # Take the longest/most specific match
        material = max(matches, key=len)
        return material.strip()

    return None


def extract_care_instructions(description: str) -> str | None:
    """Extract care instructions from description text."""
    if not description:
        return None

    # Look for common care instruction keywords
    care_patterns = [
        r"(?:care|wash|clean|machine wash|hand wash|dry clean|dry flat|no (?:shrinkage|pilling)|shrinkage|pilling)[^.!?]*[.!?]",
    ]

    care_info = []
    for pattern in care_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        care_info.extend(matches)

    if care_info:
        # Deduplicate and join
        unique_care = list(dict.fromkeys(care_info))
        return " ".join(unique_care[:2])  # Take top 2

    return None


def extract_sizing_info(description: str) -> str | None:
    """Extract sizing/fit information from description text."""
    if not description:
        return None

    # Look for model info and sizing guidance
    sizing_patterns = [
        r"(?:model is|wearing|sizing|size recommendation|true to size|fit|loose fit|fitted)[^.!?]*[.!?]",
    ]

    sizing_info = []
    for pattern in sizing_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        sizing_info.extend(matches)

    if sizing_info:
        # Deduplicate and join (take first 2)
        unique_sizing = list(dict.fromkeys(sizing_info))
        return " ".join(unique_sizing[:2])

    return None


def build_search_text(
    title: str,
    vendor: str | None,
    description: str | None,
    material: str | None,
    care: str | None,
    sizing: str | None,
    colors: list[str] | None,
    sizes: list[str] | None,
    product_type: str | None,
    tags: list[str] | None,
) -> str:
    """
    Build optimized search text for vector embedding.

    Format:
    "{title} by {vendor}. {description}. {product_type}. Material: {material}. 
    Care: {care}. Sizing: {sizing}. Available in sizes: {sizes}. Colors: {colors}. Tags: {tags}"
    """
    parts = [title]

    if vendor:
        parts.append(f"by {vendor}")

    if product_type:
        parts.append(f"Type: {product_type}")

    if description:
        parts.append(description)

    if material:
        parts.append(f"Material: {material}")

    if care:
        parts.append(f"Care: {care}")

    if sizing:
        parts.append(f"Sizing: {sizing}")

    if sizes:
        parts.append(f"Available sizes: {', '.join(sizes)}")

    if colors:
        parts.append(f"Available colors: {', '.join(colors)}")

    if tags:
        parts.append(f"Tags: {', '.join(tags)}")

    # Join with periods and clean up
    search_text = ". ".join(parts)
    search_text = re.sub(r"\s+", " ", search_text).strip()
    return search_text


def extract_variant_attributes(option1: str | None, option2: str | None, option3: str | None) -> tuple[str | None, str | None]:
    """
    Extract size and color from variant options.
    Handles different option orderings (Size/Color, Color/Size, etc.)
    """
    size_keywords = {"size", "s", "m", "l", "xl", "xs", "xxl", "one", "free"}
    color_keywords = {"color", "colour", "red", "blue", "green", "white", "black", "navy", "grey", "gray"}

    options = [opt for opt in [option1, option2, option3] if opt]
    size = None
    color = None

    for opt in options:
        opt_lower = opt.lower()
        # Check if it's likely a size
        if any(keyword in opt_lower for keyword in size_keywords):
            size = opt
        # Check if it's likely a color
        elif any(keyword in opt_lower for keyword in color_keywords):
            color = opt
        # Heuristic: single/double letter or known sizes are likely size
        elif len(opt) <= 2 and opt.upper() in {"S", "M", "L", "XL", "XXL", "XS"}:
            size = opt
        # Otherwise treat as color if not assigned
        elif not color:
            color = opt

    return size, color


def build_vectordb_payload(
    product_data: dict[str, Any],
    store_id: int,
    product_id: int,
) -> dict[str, Any]:
    """
    Transform raw Shopify product data into VectorDB-optimized payload.
    """
    shopify_id = product_data.get("id")
    title = product_data.get("title", "")
    vendor = product_data.get("vendor")
    product_type = product_data.get("product_type")
    tags = product_data.get("tags", [])
    published_at = product_data.get("published_at")
    updated_at = product_data.get("updated_at")

    # Clean description
    raw_html = product_data.get("body_html")
    description_clean = clean_html(raw_html)

    # Extract metadata
    material = extract_material_info(description_clean) if description_clean else None
    care = extract_care_instructions(description_clean) if description_clean else None
    sizing = extract_sizing_info(description_clean) if description_clean else None

    # Process variants and aggregate options
    variants = product_data.get("variants", [])
    available_sizes = set()
    available_colors = set()
    prices = []
    all_available = False
    all_image_urls = {}  # color -> url mapping

    for variant in variants:
        if not isinstance(variant, dict):
            continue

        option1 = variant.get("option1")
        option2 = variant.get("option2")
        option3 = variant.get("option3")

        size, color = extract_variant_attributes(option1, option2, option3)
        if size:
            available_sizes.add(size)
        if color:
            available_colors.add(color)

        if variant.get("available"):
            all_available = True

        price = variant.get("price")
        if price:
            try:
                prices.append(float(price))
            except (ValueError, TypeError):
                pass

        # Store primary image for each color
        featured_img = variant.get("featured_image")
        if featured_img and isinstance(featured_img, dict):
            img_src = featured_img.get("src")
            if img_src and color:
                # Only store unique images (first color variant per image)
                if img_src not in all_image_urls.values():
                    all_image_urls[color] = img_src

    # Get primary image (first by position)
    images = product_data.get("images", [])
    primary_image_url = None
    if images and isinstance(images[0], dict):
        primary_image_url = images[0].get("src")

    # Sort and convert to lists
    available_sizes = sorted(list(available_sizes))
    available_colors = sorted(list(available_colors))
    all_image_urls_list = list(all_image_urls.values())

    # Calculate price range
    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None

    # Build search text
    search_text = build_search_text(
        title=title,
        vendor=vendor,
        description=description_clean,
        material=material,
        care=care,
        sizing=sizing,
        colors=available_colors,
        sizes=available_sizes,
        product_type=product_type,
        tags=tags,
    )

    return {
        "store_id": store_id,
        "product_id": product_id,
        "shopify_product_id": shopify_id,
        "title": title,
        "description_clean": description_clean,
        "vendor": vendor,
        "product_type": product_type,
        "tags": tags,
        "material": material,
        "care_instructions": care,
        "sizing_info": sizing,
        "fit_description": None,  # Could parse from sizing info if needed
        "available_colors": available_colors,
        "available_sizes": available_sizes,
        "all_available": all_available,
        "primary_image_url": primary_image_url,
        "all_image_urls": all_image_urls_list,
        "min_price": min_price,
        "max_price": max_price,
        "search_text": search_text,
        "published_at": published_at,
        "shopify_updated_at": updated_at,
    }
