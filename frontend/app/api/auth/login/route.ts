import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST(request: NextRequest) {
  try {
    const { username, password } = await request.json();

    // Define allowed users from environment variables
    const allowedUsers: { [key: string]: string } = {
      [process.env.ADMIN_USERNAME || '']: process.env.ADMIN_PASSWORD || '',
      [process.env.USER2_USERNAME || '']: process.env.USER2_PASSWORD || '',
      [process.env.USER3_USERNAME || '']: process.env.USER3_PASSWORD || '',
      [process.env.USER4_USERNAME || '']: process.env.USER4_PASSWORD || '',
      [process.env.USER5_USERNAME || '']: process.env.USER5_PASSWORD || '',
      // Add more users as needed...
    };

    // Remove empty entries
    Object.keys(allowedUsers).forEach(key => {
      if (!key || !allowedUsers[key]) {
        delete allowedUsers[key];
      }
    });

    // Validate that at least one user is configured
    if (Object.keys(allowedUsers).length === 0) {
      return NextResponse.json(
        { message: 'Authentication not configured' },
        { status: 500 }
      );
    }

    // Check if credentials match any allowed user
    if (allowedUsers[username] && allowedUsers[username] === password) {
      // Set secure session cookie
      const cookieStore = await cookies();
      cookieStore.set('authenticated', 'true', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/',
      });

      // Store username in cookie for display
      cookieStore.set('username', username, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 60 * 60 * 24 * 7,
        path: '/',
      });

      return NextResponse.json({ success: true, message: 'Login successful' });
    }

    // Invalid credentials
    return NextResponse.json(
      { success: false, message: 'Invalid username or password' },
      { status: 401 }
    );
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { message: 'An error occurred during login' },
      { status: 500 }
    );
  }
}
