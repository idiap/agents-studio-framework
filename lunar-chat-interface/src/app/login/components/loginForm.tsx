// Copyright © 2024 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo.gusicuma@idiap.ch>
//
// SPDX-License-Identifier: GPL-3.0-or-later

"use client"
import { signIn } from "next-auth/react";
import Image from "next/image"
import url from "@/assets/brand.png"
import Button from "@/components/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface LoginFormProps {
  bypassAuthentication: boolean
  defaultUser: string
}

const LoginForm: React.FC<LoginFormProps> = ({ bypassAuthentication, defaultUser }) => {
  const router = useRouter();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (bypassAuthentication) {
      const signInResult = await signIn("credentials", {
        redirect: false,
        login: defaultUser,
        password: defaultUser,
      });
      if (signInResult?.ok) {
        router.push("/app");
        return;
      }
      setError("Bypass authentication failed.");
      return;
    }

    if (!login || !password) {
      setError("Login and password are required.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      if (mode === "register") {
        const registerResponse = await fetch("/api/auth/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            login,
            password,
          }),
        });

        if (!registerResponse.ok) {
          const registerError = await registerResponse.json().catch(() => ({}));
          setError(registerError.detail || registerError.error || "Registration failed.");
          return;
        }
      }

      const signInResult = await signIn("credentials", {
        redirect: false,
        login,
        password,
      });

      if (!signInResult?.ok) {
        setError("Invalid login or password.");
        return;
      }

      router.push("/app");
      router.refresh();
    } catch (submitError) {
      console.error("Authentication failed:", submitError);
      setError("Authentication failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return <div className="flex flex-col items-center mt-10">
    <Image alt="Lunar" src={url} width={250} height={64} className="mb-8" />
    <h2 className="text-white">Welcome to the <span>Lunarverse</span>!</h2>
    <form
      onSubmit={handleSubmit}
      className="max-w-[400px] mx-auto w-full mt-16 space-y-4"
      autoComplete="off"
    >
      {bypassAuthentication ? (
        <Button
          variant="primary"
          className="w-full"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Starting..." : "Start using Lunar"}
        </Button>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 rounded-md overflow-hidden border border-white/20">
            <button
              type="button"
              className={`py-2 text-sm ${mode === "login" ? "bg-white text-black" : "bg-transparent text-white"}`}
              onClick={() => setMode("login")}
            >
              Login
            </button>
            <button
              type="button"
              className={`py-2 text-sm ${mode === "register" ? "bg-white text-black" : "bg-transparent text-white"}`}
              onClick={() => setMode("register")}
            >
              Register
            </button>
          </div>
          <Input placeholder="Login" className="text-white" value={login} onChange={(e) => setLogin(e.target.value)} />
          <Input placeholder="Password" type="password" className="text-white" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm text-red-300">{error}</p>}
          <Button
            variant="primary"
            className="w-full flex items-center justify-center gap-2"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? mode === "register"
                ? "Registering..."
                : "Logging in..."
              : mode === "register"
                ? "Create account"
                : "Login"}
          </Button>
        </div>
      )}
    </form>
  </div>
}

export default LoginForm
