const json = (data, status=200) => Response.json(data,{status,headers:{"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}});
export default {
 async fetch(request, env) {
  const url = new URL(request.url);
  if (url.pathname !== "/api/instagram") return env.ASSETS.fetch(request);
  if (request.method !== "GET") return json({error:"Método no permitido"},405);
  if (!env.INSTAGRAM_ACCESS_TOKEN) return json({error:"Integración pendiente de configurar"},503);
  const key = new Request(url.origin + "/api/instagram");
  const cached = await caches.default.match(key);
  if (cached) return cached;
  try {
   const endpoint = new URL("https://graph.facebook.com/v27.0/17841437480247825/media");
   endpoint.searchParams.set("fields","id,caption,media_type,permalink,media_url,thumbnail_url,timestamp");
   endpoint.searchParams.set("limit","6");
   const response = await fetch(endpoint,{headers:{Authorization:"Bearer "+env.INSTAGRAM_ACCESS_TOKEN}});
   if (!response.ok) return json({error:"Instagram no disponible"},502);
   const result = await response.json();
   if (!Array.isArray(result.data)) return json({error:"Respuesta inesperada"},502);
   const data = result.data.map(({id,caption,media_type,permalink,media_url,thumbnail_url,timestamp})=>({id,caption,media_type,permalink,media_url,thumbnail_url,timestamp}));
   const output = Response.json({data},{headers:{"Cache-Control":"public, max-age=300","X-Content-Type-Options":"nosniff"}});
   await caches.default.put(key,output.clone());
   return output;
  } catch { return json({error:"Instagram no disponible"},502); }
 }
};
