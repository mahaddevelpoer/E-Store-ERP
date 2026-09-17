-- ====================================================================
-- Production Database Schema for Electronics Accessories & Media System
-- Classic Business Standard Schema (Compatible with Supabase PostgreSQL)
-- ====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Shop Business & Settings Table
CREATE TABLE IF NOT EXISTS public.shop_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_name TEXT NOT NULL DEFAULT 'ElectroStore Accessories & Media',
    phone TEXT DEFAULT '',
    address TEXT DEFAULT '',
    theme_mode TEXT NOT NULL DEFAULT 'Dark',
    currency TEXT NOT NULL DEFAULT 'PKR',
    receipt_footer TEXT DEFAULT 'Thank you for visiting! Software & Media items non-refundable.',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed Default Settings
INSERT INTO public.shop_settings (shop_name, phone, address, theme_mode, currency)
VALUES ('ElectroStore Accessories & Media', '+92 300 1234567', 'Main Electronics Market', 'Dark', 'PKR')
ON CONFLICT DO NOTHING;

-- 2. Device Pairings Table (Dynamic 6-Digit OTP)
CREATE TABLE IF NOT EXISTS public.device_pairings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pair_code VARCHAR(6) UNIQUE NOT NULL,
    fcm_token TEXT,
    device_name TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Categories Table
CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.categories (name) VALUES 
('Chargers & Adapters'),
('USB & Data Cables'),
('Wireless Earbuds & Headphones'),
('Mobile Covers & Cases'),
('Screen Protectors'),
('Powerbanks'),
('Smartwatches & Bands'),
('Car Accessories'),
('USB Media & Copying Services')
ON CONFLICT (name) DO NOTHING;

-- 4. Products Inventory Table
CREATE TABLE IF NOT EXISTS public.products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    category_name TEXT NOT NULL DEFAULT 'General',
    barcode TEXT UNIQUE,
    cost_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    selling_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    stock_quantity INT NOT NULL DEFAULT 0,
    low_stock_threshold INT NOT NULL DEFAULT 5,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Sales Transactions Table (With Split Hardware vs Media Service Revenue)
CREATE TABLE IF NOT EXISTS public.sales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_number TEXT UNIQUE NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    hardware_revenue NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    media_service_revenue NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_profit NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    payment_method TEXT NOT NULL DEFAULT 'Cash',
    discount NUMERIC(10, 2) DEFAULT 0.00,
    item_count INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Sale Items Table (With Item Type Tag: 'Hardware' or 'MediaService')
CREATE TABLE IF NOT EXISTS public.sale_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_id UUID REFERENCES public.sales(id) ON DELETE CASCADE,
    product_id UUID REFERENCES public.products(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL,
    item_type TEXT NOT NULL DEFAULT 'Hardware', -- 'Hardware' or 'MediaService'
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_price NUMERIC(10, 2) NOT NULL
);

-- 7. Udhaar Ledger Table
CREATE TABLE IF NOT EXISTS public.udhaar_ledger (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    party_name TEXT NOT NULL,
    party_type TEXT NOT NULL CHECK (party_type IN ('Customer', 'Supplier')),
    amount NUMERIC(10, 2) NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('Given', 'Received')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Realtime Subscriptions
ALTER PUBLICATION supabase_realtime ADD TABLE public.products;
ALTER PUBLICATION supabase_realtime ADD TABLE public.sales;
ALTER PUBLICATION supabase_realtime ADD TABLE public.device_pairings;

-- DB Trigger Function for Instant Mobile Push Notification
CREATE OR REPLACE FUNCTION notify_sale_event()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM
    net.http_post(
      url := (SELECT value FROM secrets.vault WHERE name = 'EDGE_FUNCTION_URL' LIMIT 1),
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer ' || (SELECT value FROM secrets.vault WHERE name = 'ANON_KEY' LIMIT 1)
      ),
      body := jsonb_build_object(
        'event', 'NEW_SALE',
        'receipt_number', NEW.receipt_number,
        'total_amount', NEW.total_amount,
        'hardware_revenue', NEW.hardware_revenue,
        'media_service_revenue', NEW.media_service_revenue,
        'total_profit', NEW.total_profit,
        'item_count', NEW.item_count
      )
    );
  RETURN NEW;
EXCEPTION WHEN OTHERS THEN
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_notify_sale ON public.sales;
CREATE TRIGGER trg_notify_sale
AFTER INSERT ON public.sales
FOR EACH ROW EXECUTE FUNCTION notify_sale_event();
