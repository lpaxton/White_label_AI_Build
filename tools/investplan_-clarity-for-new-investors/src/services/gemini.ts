import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

export interface InvestmentProfile {
  goal: string;
  timeline: number;
  monthlyContribution: number;
  startingAmount: number;
}

export async function getActionPlan(profile: InvestmentProfile) {
  const prompt = `
    I am a complete beginner focusing on a specific goal.
    Goal: "${profile.goal}"
    Timeline: ${profile.timeline} years

    Please provide a simple "Growth Lesson" for a beginner that explains how money grows for their specific situation:
    1. Vision: A 1-sentence supportive reflection on why "${profile.goal}" is a goal worth starting for today.
    2. Principle: A 1-3 word name for a financial principle that fits this ${profile.timeline}-year window (e.g., "Compound Interest", "Dollar-Cost Averaging", "The Time Advantage").
    3. Perspective: A "Learning Moment" explanation. Specifically explain the GROWTH MECHANIC appropriate for their ${profile.timeline}-year timeline. For short terms (<5 years), focus on the power of starting and consistency. For long terms (>10 years), focus on how time does the heavy lifting through compounding. Use simple, non-technical language that makes them feel like they've learned something new about how money works.

    Keep it educational, inspiring, and very brief (max 3 sentences total). Do NOT provide financial advice.
    
    Format the response as JSON with three string fields: "vision", "principle", and "perspective".
  `;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
      }
    });

    const parsed = JSON.parse(response.text || "{}");
    return {
      vision: parsed.vision || `Building a foundation for ${profile.goal}.`,
      principle: parsed.principle || (profile.timeline >= 10 ? "Compound Interest" : "Consistency habit"),
      perspective: parsed.perspective || `By sticking to $${profile.monthlyContribution} for ${profile.timeline} years, you're using the power of persistence to turn a small habit into a significant destination.`
    };
  } catch (error) {
    console.error("Gemini Error:", error);
    return {
      vision: `Building a foundation for ${profile.goal}.`,
      principle: profile.timeline >= 10 ? "Compound Interest" : "Consistency habit",
      perspective: `By sticking to $${profile.monthlyContribution} for ${profile.timeline} years, you're using the power of persistence to turn a small habit into a significant destination.`
    };
  }
}
