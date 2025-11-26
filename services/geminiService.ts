import { GoogleGenAI, Type } from "@google/genai";
import { LogEntry } from '../types';

const API_KEY = process.env.API_KEY;
// Initialize AI only if key exists
const ai = API_KEY ? new GoogleGenAI({ apiKey: API_KEY }) : null;

export const analyzeSecurityLogs = async (logs: LogEntry[]) => {
    if (!ai) {
        console.warn("Gemini API Key missing. Returning mock analysis.");
        return {
            summary: "Demo Mode: API Key missing. Showing simulated analysis based on recent logs.",
            threatScore: 45,
            recommendations: [
                "Configure API Key in .env file to enable real AI analysis",
                "Review recent login attempts manually",
                "Check system for unauthorized port access"
            ],
            flaggedLogs: logs.slice(0, 2).map(l => l.id)
        };
    }

    try {
        const model = 'gemini-2.5-flash';
        const logData = JSON.stringify(logs.slice(0, 20)); // Analyze last 20 logs to save tokens/context

        const prompt = `
        You are Sentinel AI, an advanced cybersecurity and behavioral analyst system.
        Analyze the following system logs for a monitoring dashboard (Parental Control or Employee Monitoring context).

        Logs:
        ${logData}

        Your task:
        1. Identify any critical security threats or policy violations.
        2. Summarize the general user behavior patterns.
        3. Calculate a "Threat Score" from 0 (Safe) to 100 (Critical).
        4. Provide 3 specific actionable recommendations for the administrator.

        Return the response in strictly valid JSON format matching this schema:
        {
            "summary": "string",
            "threatScore": number,
            "recommendations": ["string", "string", "string"],
            "flaggedLogs": ["id1", "id2"]
        }
        `;

        const response = await ai.models.generateContent({
            model: model,
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        summary: { type: Type.STRING },
                        threatScore: { type: Type.NUMBER },
                        recommendations: {
                            type: Type.ARRAY,
                            items: { type: Type.STRING }
                        },
                        flaggedLogs: {
                            type: Type.ARRAY,
                            items: { type: Type.STRING }
                        }
                    }
                }
            }
        });

        const text = response.text;
        if (!text) throw new Error("No response from AI");
        
        return JSON.parse(text);

    } catch (error) {
        console.error("Error analyzing logs:", error);
        throw error;
    }
};

export const chatWithAnalyst = async (message: string, contextLogs: LogEntry[]) => {
    if (!ai) {
        return "I am currently in Demo Mode because no API Key was provided. Please configure the GEMINI_API_KEY to enable live chat analysis.";
    }

    try {
         const model = 'gemini-2.5-flash';
         const context = JSON.stringify(contextLogs.slice(0, 10));
         
         const response = await ai.models.generateContent({
             model: model,
             contents: `
             Context: The following are recent security logs: ${context}.
             User Question: ${message}
             
             Answer as a helpful cybersecurity expert. Keep it concise.
             `,
         });
         return response.text;
    } catch (error) {
        console.error("Chat error:", error);
        return "System error: Unable to process request.";
    }
}
