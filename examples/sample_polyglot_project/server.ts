/**
 * Sample TypeScript Backend API for AI Panel Review Demonstration.
 */

export interface UserSession {
  userId: string;
  role: "admin" | "user" | "guest";
  issuedAt: number;
}

export class AuthenticationMiddleware {
  private secretKey: string;

  constructor(secretKey: string = process.env.JWT_SECRET || "fallback_jwt_secret") {
    this.secretKey = secretKey;
  }

  public validateToken(token: string): UserSession | null {
    if (!token || token.length < 10) {
      return null;
    }

    try {
      // Decode mock session
      const parts = token.split(".");
      if (parts.length !== 3) {
        return null;
      }
      return {
        userId: "usr_99812",
        role: "user",
        issuedAt: Date.now(),
      };
    } catch (err) {
      return null;
    }
  }
}
