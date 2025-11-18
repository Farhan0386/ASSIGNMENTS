# 📂 README.md

```markdown
# CSS Positioning & Basic Layout – Summary Notes

This project contains **summary notes** for Lecture 13: *CSS Positioning & Basic Layout*.  
It is split into two files:
- `index.html` → Structured notes with definitions, meanings, and examples.
- `style.css` → Styling and positioning examples with comments.

---

## 📖 Contents

### 1. Introduction
- CSS positioning controls where elements appear on a webpage.
- By default, elements stack top-to-bottom.
- Positioning allows movement, layering, and flexible layouts.

### 2. Types of CSS Positioning
- **Static** → Default, elements follow normal flow.
- **Relative** → Element stays in flow but can be shifted using `top`, `left`, `right`, `bottom`.
- **Absolute** → Removed from flow, positioned relative to nearest positioned ancestor.
- **Fixed** → Stays fixed relative to viewport (does not move on scroll).
- **Sticky** → Acts like relative until a scroll threshold, then sticks.

---

## 💻 Examples

### Static Position
```css
.static {
  background-color: lightblue;
  position: static; /* Default, cannot be moved */
}
```

### Relative Position

```css
.relative {
  background-color: lightgreen;
  position: relative; /* Moves relative to normal spot */
  top: 20px; /* Shift down */
  left: 30px; /* Shift right */
}
```

### Absolute Position

```css
.container {
  position: relative; /* Establishes positioning context */
  width: 300px;
  height: 200px;
  background-color: #f0f0f0;
  border: 1px solid #000;
}

.absolute {
  background-color: coral;
  position: absolute; /* Positioned relative to container */
  top: 50px;
  left: 50px;
}
```
