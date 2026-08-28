---
name: Lumina Finance
colors:
  surface: '#0f131d'
  surface-dim: '#0f131d'
  surface-bright: '#353944'
  surface-container-lowest: '#0a0e18'
  surface-container-low: '#171b26'
  surface-container: '#1c1f2a'
  surface-container-high: '#262a35'
  surface-container-highest: '#313540'
  on-surface: '#dfe2f1'
  on-surface-variant: '#bacac1'
  inverse-surface: '#dfe2f1'
  inverse-on-surface: '#2c303b'
  outline: '#85948c'
  outline-variant: '#3c4a43'
  surface-tint: '#2fe0aa'
  primary: '#44edb7'
  on-primary: '#003828'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#006c4f'
  secondary: '#4cd7f6'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#d1d3d5'
  on-tertiary: '#2e3132'
  tertiary-container: '#b6b7b9'
  on-tertiary-container: '#46484a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#e1e2e4'
  tertiary-fixed-dim: '#c5c6c8'
  on-tertiary-fixed: '#191c1e'
  on-tertiary-fixed-variant: '#444749'
  background: '#0f131d'
  on-background: '#dfe2f1'
  surface-variant: '#313540'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-max: 1440px
  gutter: 24px
  margin-desktop: 40px
  margin-mobile: 16px
  stack-xs: 4px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
  stack-xl: 48px
---

## Brand & Style

The design system is engineered for a high-performance financial AI environment. The brand personality is precise, forward-thinking, and authoritative, yet accessible through intuitive data visualization. 

The aesthetic leverages **Dark-Mode Glassmorphism** and **Cyber-Professionalism**. It combines the structured reliability of a traditional fintech dashboard with the energetic, high-tech signals of artificial intelligence. Visual cues prioritize clarity of information, using vibrant accent "glows" to draw attention to critical insights, growth trends, and AI-generated suggestions. The interface should feel like a premium command center—liquid, responsive, and deeply integrated.

## Colors

The palette is optimized for long-session legibility in a dark environment.

- **Primary Background:** Deep Slate (#0B0F19) provides a high-contrast base that makes neon accents pop without causing eye strain.
- **Surface Layering:** Surfaces use a semi-transparent Navy (#151C2C). When layered, these should utilize a `backdrop-filter: blur(12px)` to create depth.
- **Accents:** 
    - **Emerald Green (#00D09C):** Used for "Growth," "Success," "AI Insights," and primary action buttons.
    - **Neon Cyan (#06B6D4):** Used for secondary data streams, information icons, and interactive hover states.
- **Typography & Details:** Crisp White (#F3F4F6) is reserved for primary text, while muted variations of the border color are used for secondary labels.

## Typography

The typography system relies on **Inter** for its neutral, highly legible, and systematic qualities. 

- **Headlines:** Use tight letter-spacing and bold weights to establish a strong hierarchy.
- **Data Display:** For financial figures and ticker symbols, use a monospaced font (JetBrains Mono) to ensure tabular alignment and numerical clarity.
- **Scaling:** On mobile, display and headline sizes are aggressively reduced to maintain information density without horizontal scrolling.
- **Hierarchy:** Use white (#F3F4F6) for H1-H3, and 70% opacity white for body text to maintain a sophisticated tonal balance.

## Layout & Spacing

This design system uses a **12-column fluid grid** for desktop and a **4-column grid** for mobile. 

- **Rhythm:** An 8px linear scale governs all spacing (8, 16, 24, 32, 48, 64).
- **Dashboard Layout:** Utilizes a fixed left-hand navigation sidebar (240px) with a fluid content area. 
- **Information Density:** Financial data tables should use compact vertical padding (12px), while marketing or landing pages should utilize the "stack-xl" (48px) units to create breathing room.
- **Safe Areas:** Ensure a minimum 16px margin on mobile devices to prevent content from hitting the screen edges.

## Elevation & Depth

Depth is signaled through **translucency and luminosity** rather than traditional shadows.

- **Level 0 (Background):** Solid #0B0F19.
- **Level 1 (Cards/Panels):** Semi-transparent #151C2C (80% opacity) with a 1px solid border (#232E42).
- **Level 2 (Modals/Popovers):** Higher opacity background with a subtle "Emerald Glow"—a 0px 4px 20px rgba(0, 208, 156, 0.15) outer shadow.
- **Interactive States:** Buttons and active cards utilize a "Neon Stroke" effect, where the border color transitions from the muted navy to the vibrant Emerald Green upon hover or selection.

## Shapes

The design system employs a **2XL roundedness** philosophy to soften the technical nature of fintech data.

- **Standard Elements:** Buttons, input fields, and small widgets use `rounded-lg` (1rem).
- **Main Containers:** Dashboard cards and primary containers use `rounded-xl` (1.5rem) to create a clear "object" feel against the background.
- **Media/Avatars:** Use circular masks for user profiles, but rounded-xl for AI assistant avatars to distinguish between human and machine entities.

## Components

### Buttons
- **Primary:** Background #00D09C, text #0B0F19, bold weight. On hover, apply a `box-shadow: 0 0 15px rgba(0, 208, 156, 0.5)`.
- **Ghost:** Border 1px #232E42, text #F3F4F6. On hover, background becomes 10% white.

### Input Fields
- Dark slate background (#0B0F19), 1px border (#232E42). 
- Focus state: Border changes to #06B6D4 with a subtle cyan outer glow.

### Cards (Glassmorphism)
- Background: rgba(21, 28, 44, 0.8).
- Backdrop-blur: 12px.
- Border: 1px solid rgba(35, 46, 66, 0.5).

### AI Insight Chips
- Compact, pill-shaped indicators with a #00D09C background at 10% opacity and a solid green left-side accent bar (2px).

### Data Visualizations
- Use the **Neon Cyan** for historical data and **Emerald Green** for projected/AI-predicted data. All chart lines should have a 2px stroke width and a subtle "neon" drop shadow of the same color.