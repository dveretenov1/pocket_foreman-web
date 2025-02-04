import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  console.log('Middleware: Checking path:', pathname);

  // Skip middleware for api routes and static files
  if (
    pathname.startsWith('/api') || 
    pathname.startsWith('/_next') || 
    pathname.includes('/static/') ||
    pathname.includes('.') // Skip files with extensions
  ) {
    return NextResponse.next();
  }

  const publicPaths = ['/login', '/signup'];
  const isPublicPath = publicPaths.some(path => pathname.startsWith(path));
  
  const token = request.cookies.get('session')?.value;
  console.log('Middleware: Session token present:', !!token);

  // If the user is on a public path but has a token, redirect to chat
  if (isPublicPath && token) {
    console.log('Middleware: Redirecting authenticated user to chat');
    return NextResponse.redirect(new URL('/chat', request.url));
  }

  // If the user is on a protected path but has no token, redirect to login
  if (!isPublicPath && !token && pathname !== '/') {
    console.log('Middleware: Redirecting unauthenticated user to login');
    return NextResponse.redirect(new URL('/login', request.url));
  }

  console.log('Middleware: Allowing request to proceed');
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * 1. /api routes
     * 2. /_next (Next.js internals)
     * 3. /static (static files)
     * 4. all root files inside /public (e.g. /favicon.ico)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};