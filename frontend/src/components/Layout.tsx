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
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

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
    { text: 'Upload Documents', icon: <UploadIcon />, path: '/upload' },
    { text: 'Jobs', icon: <JobsIcon />, path: '/jobs' },
    { text: 'Approvals', icon: <ApprovalIcon />, path: '/approvals' },
  ];

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar sx={{ justifyContent: 'center', py: 2 }}>
        {/* Eventual Logo */}
        <img 
          src="/logo.Eventual_100x74_transparent.png" 
          alt="Eventual Logo" 
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
            Agent2 Document Ingestor
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