# PBS_SYSTEM
SAP Integrated Budget System - DEMO

# 💰 PBS System - Budget Management

Corporate Budget Planning and Management System with modern UI/UX.

## 🎯 Features

- **Dashboard** - Budget overview with charts and analytics
- **Data Management** - Company, Product, Customer management  
- **Analytics** - Detailed analysis and visualizations
- **Excel-like Data Entry** - Copy/paste, keyboard navigation
- **Collapsible Sidebar** - SAP-style professional UI
- **Responsive Design** - Works on all devices

## 🛠️ Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS
- **UI**: TanStack Table, Recharts, Lucide Icons
- **Routing**: React Router v6
- **State**: Zustand
- **API**: Axios

## 📦 Installation
```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure
```
frontend/
├── src/
│   ├── components/      # Reusable components
│   │   ├── LayoutProvider.tsx
│   │   ├── EnhancedDataGridTable.tsx
│   │   └── ...
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   ├── DataEntryPage.tsx
│   │   └── AnalyticsDashboard.tsx
│   ├── api/            # API clients
│   ├── stores/         # Zustand stores
│   └── App.tsx
├── tailwind.config.js
└── package.json
```

## 🚀 Usage

1. Login with credentials
2. Navigate between Dashboard, Data Entry, Analytics
3. Manage master data (Companies, Products, Customers)
4. View analytics and reports

## 📸 Screenshots

- Dashboard with budget overview
- Data entry with Excel-like grid
- Analytics with multiple charts

## 📝 License

MIT

## 👨‍💻 Author

dataXmagician
