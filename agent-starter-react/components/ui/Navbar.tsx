'use client';

import Link from 'next/link';
import { User, Zap } from 'lucide-react';
import { Button } from './ui/button';

const Navbar = () => {
  return (
    <nav className="border-border bg-background/80 fixed top-0 right-0 left-0 z-50 border-b backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="group flex items-center gap-2">
          <div className="relative">
            <Zap className="text-primary animate-pulse-glow h-7 w-7" />
            <div className="bg-primary/20 animate-pulse-glow absolute inset-0 rounded-full blur-xl" />
          </div>
          <span className="bg-gradient-primary bg-clip-text text-xl font-bold text-transparent">
            Nexus
          </span>
        </Link>

        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm">
              Dashboard
            </Button>
          </Link>
          <Link href="/profile">
            <Button variant="ghost" size="icon">
              <User className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="/signin">
            <Button size="sm">Sign In</Button>
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
