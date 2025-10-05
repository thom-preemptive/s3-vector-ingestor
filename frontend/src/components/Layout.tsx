import React from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  CloudUpload as UploadIcon,
  Assignment as JobsIcon,
  CheckCircle as ApprovalIcon,
  ExitToApp as SignOutIcon,
  Language as UrlIcon,
  BugReport as DiagnosticIcon,
  Description as DescriptionIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import versionInfo from '../version.json';

const drawerWidth = 225;

interface LayoutProps {
  user: any;
  signOut?: () => void;
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ user, signOut, children }) => {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Debug: Log user object to understand its structure
  React.useEffect(() => {
    console.log('User object:', user);
  }, [user]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Upload Files', icon: <UploadIcon />, path: '/upload' },
    { text: 'Scrape URL', icon: <UrlIcon />, path: '/url-scraping' },
    { text: 'Jobs', icon: <JobsIcon />, path: '/jobs' },
    { text: 'Documents', icon: <DescriptionIcon />, path: '/documents' },
    { text: 'Approvals', icon: <ApprovalIcon />, path: '/approvals' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
    { text: 'Diagnostics', icon: <DiagnosticIcon />, path: '/diagnostics' },
    { text: 'User Guide', icon: <HelpIcon />, path: '/user-guide' },
  ];

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar sx={{ justifyContent: 'center', py: 2 }}>
        {/* Eventual Logo */}
        <img 
          src="/ingestor.png" 
          alt="Ingestor Logo" 
          style={{ 
            height: '50px', 
            width: 'auto',
            maxWidth: '180px',
            objectFit: 'contain'
          }} 
        />
      </Toolbar>
      
      {/* Navigation Menu */}
      <List sx={{ flexGrow: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              sx={{
                py: 1, // Reduce vertical padding by 50%
                '& .MuiListItemIcon-root': {
                  minWidth: '32px', // Reduce icon spacing by 50%
                },
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Sign Out Button at Bottom */}
      <Box sx={{ p: 2 }}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<SignOutIcon />}
          onClick={signOut || (() => {})}
          sx={{
            borderColor: '#6a37b0',
            color: '#6a37b0',
            '&:hover': {
              backgroundColor: '#6a37b0',
              color: 'white',
            },
          }}
        >
          Sign Out
        </Button>
        
        {/* Version Number */}
        <Typography 
          variant="caption" 
          sx={{ 
            display: 'block',
            textAlign: 'center',
            mt: 1,
            fontSize: '10pt',
            color: 'black',
            fontWeight: 500
          }}
        >
          ver. {versionInfo.version}
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: '#6a37b0', // Eventual's primary color
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            S3 Vector Store Ingestor
          </Typography>
          {/* Display user email in top right */}
          <Typography variant="body2" sx={{ 
            color: 'white',
            fontWeight: 500,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            padding: '4px 12px',
            borderRadius: '16px',
          }}>
            {user?.signInDetails?.loginId || user?.attributes?.email || user?.username || 'User'}
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

export default Layout;