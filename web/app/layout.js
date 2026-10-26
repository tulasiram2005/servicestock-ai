import './style.css';

export const metadata = {title: 'ServiceStock AI', description: 'ServiceStock AI workspace'};

export default function RootLayout({children}) {
  return <html lang="en"><body>{children}</body></html>;
}
