# UI Design System
Project: Signed-PDF File Organizer - Web Interface
Author: Seonghoon Yi
Date: 2025-01-21

## Overview
Design system specification for the File Organizer web interface to ensure consistent, professional, and accessible user experience.

## Design Principles
1. **Clarity**: Information is easy to find and understand
2. **Efficiency**: Common tasks require minimal clicks
3. **Reliability**: Visual feedback confirms system state
4. **Simplicity**: Interface doesn't overwhelm non-technical users

## Color Palette

### Primary Colors
- **Primary Blue**: `#2563eb` (buttons, links, active states)
- **Primary Blue Dark**: `#1d4ed8` (hover states)
- **Primary Blue Light**: `#dbeafe` (backgrounds, subtle highlights)

### Status Colors
- **Success Green**: `#16a34a` (service running, successful operations)
- **Success Green Light**: `#dcfce7` (success backgrounds)
- **Warning Yellow**: `#d97706` (warnings, pending states)
- **Warning Yellow Light**: `#fef3c7` (warning backgrounds)
- **Error Red**: `#dc2626` (errors, service stopped)
- **Error Red Light**: `#fee2e2` (error backgrounds)

### Neutral Colors
- **Gray 900**: `#111827` (primary text)
- **Gray 700**: `#374151` (secondary text)
- **Gray 500**: `#6b7280` (muted text, placeholders)
- **Gray 200**: `#e5e7eb` (borders, dividers)
- **Gray 100**: `#f3f4f6` (backgrounds)
- **White**: `#ffffff` (card backgrounds, primary background)

## Typography

### Font Family
- **Primary**: Inter, system-ui, sans-serif
- **Monospace**: 'Fira Code', 'Courier New', monospace (for logs, file paths)

### Font Sizes & Weights
```css
/* Headings */
.text-3xl { font-size: 1.875rem; font-weight: 700; } /* Page titles */
.text-2xl { font-size: 1.5rem; font-weight: 600; }   /* Section titles */
.text-xl { font-size: 1.25rem; font-weight: 600; }   /* Card titles */
.text-lg { font-size: 1.125rem; font-weight: 500; }  /* Subheadings */

/* Body text */
.text-base { font-size: 1rem; font-weight: 400; }    /* Default text */
.text-sm { font-size: 0.875rem; font-weight: 400; }  /* Secondary text */
.text-xs { font-size: 0.75rem; font-weight: 400; }   /* Captions, timestamps */
```

## Components

### Buttons

#### Primary Button
```css
.btn-primary {
  background: #2563eb;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: background 0.2s;
}
.btn-primary:hover { background: #1d4ed8; }
.btn-primary:disabled { background: #9ca3af; cursor: not-allowed; }
```

#### Secondary Button
```css
.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
}
.btn-secondary:hover { background: #f9fafb; }
```

#### Danger Button
```css
.btn-danger {
  background: #dc2626;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
}
.btn-danger:hover { background: #b91c1c; }
```

### Status Indicators

#### Service Status Badge
```css
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-running {
  background: #dcfce7;
  color: #166534;
}

.status-stopped {
  background: #fee2e2;
  color: #991b1b;
}

.status-error {
  background: #fef3c7;
  color: #92400e;
}
```

### Cards
```css
.card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
}

.card-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}
```

### Form Elements

#### Input Fields
```css
.input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
}
.input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
.input:invalid {
  border-color: #dc2626;
}
```

#### Select Dropdowns
```css
.select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  background: white;
  cursor: pointer;
}
```

### Tables
```css
.table {
  width: 100%;
  border-collapse: collapse;
}
.table th {
  background: #f9fafb;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}
.table td {
  padding: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
}
.table tr:hover {
  background: #f9fafb;
}
```

## Layout Structure

### Main Layout
```
┌─────────────────────────────────────────────┐
│ Header (60px)                               │
├─────────────────────────────────────────────┤
│ Sidebar │ Main Content Area                 │
│ (240px) │                                   │
│         │                                   │
│         │                                   │
│         │                                   │
└─────────────────────────────────────────────┘
```

### Grid System
- **Container**: max-width 1200px, centered
- **Columns**: 12-column grid with 1rem gutters
- **Breakpoints**: 
  - sm: 640px
  - md: 768px  
  - lg: 1024px
  - xl: 1280px

## Spacing Scale
```css
.space-1 { margin/padding: 0.25rem; }  /* 4px */
.space-2 { margin/padding: 0.5rem; }   /* 8px */
.space-3 { margin/padding: 0.75rem; }  /* 12px */
.space-4 { margin/padding: 1rem; }     /* 16px */
.space-6 { margin/padding: 1.5rem; }   /* 24px */
.space-8 { margin/padding: 2rem; }     /* 32px */
.space-12 { margin/padding: 3rem; }    /* 48px */
```

## Icons
- **Icon Library**: Heroicons (outline and solid variants)
- **Size Standard**: 20px (1.25rem) for inline icons, 24px (1.5rem) for buttons
- **Colors**: Inherit text color or use semantic colors

### Common Icons
- **Service Status**: 
  - Running: CheckCircleIcon (green)
  - Stopped: XCircleIcon (red)  
  - Error: ExclamationTriangleIcon (yellow)
- **Actions**:
  - Start: PlayIcon
  - Stop: StopIcon
  - Settings: CogIcon
  - Refresh: ArrowPathIcon

## Animation & Transitions
```css
/* Standard transitions */
.transition { transition: all 0.2s ease-in-out; }
.transition-colors { transition: color, background-color 0.2s ease-in-out; }

/* Loading animations */
.loading-spinner {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Fade in/out */
.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

## Responsive Design

### Mobile-First Approach
- Default styles for mobile (320px+)
- Progressive enhancement for larger screens
- Touch-friendly targets (44px minimum)

### Key Breakpoints
- **Mobile**: Single column layout, full-width sidebar overlay
- **Tablet**: Two-column layout, collapsible sidebar  
- **Desktop**: Full layout with persistent sidebar

## Accessibility

### Color Contrast
- **Text on white**: Minimum 4.5:1 contrast ratio
- **Interactive elements**: Minimum 3:1 contrast ratio
- **Focus indicators**: High contrast, visible outline

### Keyboard Navigation
- **Tab order**: Logical sequence through interactive elements
- **Focus management**: Clear focus indicators, trapped focus in modals
- **Shortcuts**: Space/Enter for buttons, Escape to close overlays

### Screen Reader Support
- **Semantic HTML**: Proper heading hierarchy, landmark regions
- **ARIA labels**: Descriptive labels for complex interactions
- **Live regions**: Announce status changes and updates

## Error States & Loading

### Loading States
```css
.loading-skeleton {
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  animation: loading 1.5s infinite;
}
@keyframes loading {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}
```

### Error States
- **Inline errors**: Red text below form fields
- **Page-level errors**: Centered card with error icon and message
- **Network errors**: Persistent banner with retry option

### Empty States
- **No data**: Friendly illustration with helpful message
- **First-time setup**: Guided instructions for initial configuration
- **Search results**: Clear message with suggestions

This design system provides the foundation for building a consistent, professional, and accessible web interface for the File Organizer application.
