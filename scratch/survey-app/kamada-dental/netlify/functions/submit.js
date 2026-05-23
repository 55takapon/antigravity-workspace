const GAS_URL =
  "https://script.google.com/macros/s/AKfycbxzdxMR3xZbeWQ8pAltTh5ejMks3Fng5X44Y6obXDzvnSUzWhCDSWgDxTaezbiSkvB4/exec";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers: CORS, body: "" };
  }
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, headers: CORS, body: "Method Not Allowed" };
  }

  try {
    const payload = JSON.parse(event.body);

    // Honeypot: ボットが隠しフィールドを埋めた場合は静かに成功を返す
    if (payload.hp) {
      return {
        statusCode: 200,
        headers: { ...CORS, "Content-Type": "application/json" },
        body: JSON.stringify({ status: "ok" }),
      };
    }

    const safePayload = {
      rating: payload.rating,
      text: /^[=+\-@]/.test(payload.text ?? "") ? "'" + payload.text : payload.text,
    };

    const gasRes = await fetch(GAS_URL, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: JSON.stringify(safePayload),
      redirect: "follow",
    });

    if (!gasRes.ok) throw new Error(`GAS returned ${gasRes.status}`);

    return {
      statusCode: 200,
      headers: { ...CORS, "Content-Type": "application/json" },
      body: JSON.stringify({ status: "ok" }),
    };
  } catch (err) {
    return {
      statusCode: 500,
      headers: { ...CORS, "Content-Type": "application/json" },
      body: JSON.stringify({ status: "error", message: err.message }),
    };
  }
};
