// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import type { NextAuthOptions } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { serverApiUrl } from "@/configuration";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export const authOptions: NextAuthOptions = {
  secret: process.env.NEXTAUTH_SECRET as string,
  pages: {
    signIn: `${basePath}/login`,
    signOut: `${basePath}/login`,
    error: `${basePath}/login`,
  },
  providers: [
    Credentials({
      name: "Credentials",
      credentials: {
        login: { label: "Login", type: "text", placeholder: "" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const login = credentials?.login;
        const password = credentials?.password;

        if (!login || !password) {
          return null;
        }

        if (!serverApiUrl) {
          return null;
        }

        const response = await fetch(`${serverApiUrl}/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            login,
            password,
          }),
        });

        if (!response.ok) {
          return null;
        }

        const data = await response.json();
        if (!data?.user?.id || !data?.user?.login || !data?.access_token) {
          return null;
        }

        return {
          id: data.user.id as string,
          name: data.user.login as string,
          email: data.user.login as string,
          login: data.user.login as string,
          accessToken: data.access_token as string,
        };
      },
    }),
  ],
  callbacks: {
    async redirect({ url, baseUrl }) {
      if (url === baseUrl || url === `${baseUrl}/`) return `${baseUrl}/`;
      if (url.startsWith("/")) return `${baseUrl}${url}`;
      else if (new URL(url).origin === baseUrl) return url;
      return `${baseUrl}`;
    },
    async jwt({ token, account, user }) {
      if (user) {
        token.accessToken = (user as { accessToken?: string }).accessToken;
        token.userId = user.id;
        token.login =
          (user as { login?: string }).login ?? user.email ?? user.name ?? "";
      }
      token.provider = account?.provider ?? token.provider ?? "credentials";
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.provider = token.provider as string;
      session.user = {
        ...session.user,
        id: token.userId as string,
        login: token.login as string,
        email: (token.login as string) || session.user?.email || null,
        name: (token.login as string) || session.user?.name || "",
      };
      return session;
    },
  },
};
