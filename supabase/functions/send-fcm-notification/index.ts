import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') || '';
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
    const fcmServerKey = Deno.env.get('FCM_SERVER_KEY') || ''; // FCM Legacy / HTTP v1 Secret Key stored in secrets

    const supabase = createClient(supabaseUrl, supabaseServiceKey);
    const body = await req.json();

    const { event, receipt_number, total_amount, total_profit, item_count, product_name, current_stock } = body;

    // Fetch active paired FCM tokens from Supabase
    const { data: pairings, error: pairError } = await supabase
      .from('device_pairings')
      .select('fcm_token')
      .eq('status', 'paired')
      .not('fcm_token', 'is', null);

    if (pairError || !pairings || pairings.length === 0) {
      return new Response(JSON.stringify({ status: 'no_tokens_found' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const tokens = pairings.map(p => p.fcm_token);

    let title = "📦 Electronics Store Alert";
    let messageBody = "New transaction update";

    if (event === 'NEW_SALE') {
      title = "💰 New Sale Completed!";
      messageBody = `Receipt: #${receipt_number}\nAmount: PKR ${total_amount} (${item_count} items)\nEst. Profit: PKR ${total_profit}`;
    } else if (event === 'LOW_STOCK') {
      title = "⚠️ Low Stock Warning!";
      messageBody = `Item '${product_name}' is running low! Current Stock: ${current_stock}`;
    }

    // Dispatch Push Notification via FCM
    const dispatchResults = await Promise.all(tokens.map(token => {
      return fetch('https://fcm.googleapis.com/fcm/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `key=${fcmServerKey}`
        },
        body: JSON.stringify({
          to: token,
          notification: {
            title: title,
            body: messageBody,
            sound: 'default'
          },
          data: {
            event: event,
            receipt_number: receipt_number || '',
            amount: String(total_amount || 0)
          }
        })
      });
    }));

    return new Response(JSON.stringify({ success: true, count: dispatchResults.length }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
