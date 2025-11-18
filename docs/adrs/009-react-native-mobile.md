# ADR-009: React Native + Expo for Mobile Applications

## Status
Accepted

## Context
The SaltBitter dating platform requires native mobile applications for iOS and Android. Mobile is critical for dating apps:
- 80%+ of dating app usage happens on mobile
- Push notifications essential for match alerts and messages
- Camera access for profile photos
- Location services for nearby matches
- App store presence builds credibility

### Requirements
- Native performance and UX
- Code sharing between iOS and Android
- Rapid development and iteration
- Push notifications
- Deep linking (match notifications → profile view)
- Camera and photo library access
- Location services
- Offline support for viewing matches

### Options Considered

**Option A: Native Development (Swift + Kotlin)**
- Pros: Best performance, access to all platform APIs, native UX
- Cons: 2x codebase, 2x team size needed, slower feature velocity

**Option B: Flutter**
- Pros: High performance (compiled to native), single codebase, growing ecosystem
- Cons: Dart language (team knows TypeScript), smaller community than React

**Option C: React Native**
- Pros: JavaScript/TypeScript (team expertise), huge ecosystem, code sharing with web
- Cons: JavaScript bridge overhead, occasional native modules needed

**Option D: React Native + Expo**
- Pros: All React Native benefits + simplified build process, OTA updates
- Cons: Limited native module access (mitigated by custom dev clients)

## Decision
We will use **React Native with Expo SDK 49+** for iOS and Android applications.

## Rationale

### Why React Native + Expo
1. **Code Sharing**: 80-90% code shared between iOS and Android
2. **Team Expertise**: Engineers already know React and TypeScript
3. **Development Speed**: Expo abstracts native build complexity
4. **OTA Updates**: Fix bugs without App Store review (1-2 weeks saved)
5. **Mature Ecosystem**: Most npm packages work, extensive native modules
6. **Performance**: Hermes engine + new architecture approaching native performance
7. **Cost**: 1 team vs. 2 separate iOS/Android teams

### Expo Benefits
- **Managed Workflow**: No Xcode/Android Studio needed for most development
- **EAS Build**: Cloud builds for iOS and Android (CI/CD ready)
- **EAS Update**: Over-the-air updates for JavaScript changes
- **EAS Submit**: Automated App Store and Play Store submissions
- **Native Modules**: Can eject to bare workflow if needed (rare)

### Code Sharing with Web

```typescript
// Shared between web and mobile
import { useAuth } from '@/hooks/useAuth';  // ✅ Works everywhere
import { ProfileCard } from '@/components/ProfileCard';  // ✅ Shared UI
import { matchingApi } from '@/api/matching';  // ✅ Shared API client

// Platform-specific when needed
import { Platform } from 'react-native';

if (Platform.OS === 'ios') {
  // iOS-specific behavior
} else if (Platform.OS === 'android') {
  // Android-specific behavior
} else {
  // Web-specific behavior
}
```

## Implementation Details

### Project Structure

```
frontend/
├── mobile/                    # React Native + Expo app
│   ├── app/                   # Expo Router (file-based routing)
│   │   ├── (tabs)/            # Bottom tab navigation
│   │   │   ├── index.tsx      # Matches screen
│   │   │   ├── messages.tsx   # Messages screen
│   │   │   ├── profile.tsx    # Profile screen
│   │   ├── match/[id].tsx     # Match detail screen
│   │   └── _layout.tsx        # Root layout
│   ├── components/            # Shared UI components
│   ├── hooks/                 # Shared React hooks
│   ├── api/                   # API client
│   ├── assets/                # Images, fonts
│   ├── app.json               # Expo config
│   └── package.json
├── web/                       # Next.js web app (shared components)
└── shared/                    # Shared code (types, utils, API)
```

### Expo Configuration

```json
{
  "expo": {
    "name": "SaltBitter",
    "slug": "saltbitter",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "automatic",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "assetBundlePatterns": [
      "**/*"
    ],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.saltbitter.app",
      "infoPlist": {
        "NSCameraUsageDescription": "SaltBitter needs access to your camera to upload profile photos",
        "NSPhotoLibraryUsageDescription": "SaltBitter needs access to your photos to set your profile pictures",
        "NSLocationWhenInUseUsageDescription": "SaltBitter uses your location to show nearby matches"
      }
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.saltbitter.app",
      "permissions": [
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE",
        "ACCESS_FINE_LOCATION"
      ]
    },
    "plugins": [
      [
        "expo-image-picker",
        {
          "photosPermission": "SaltBitter needs access to your photos to set profile pictures"
        }
      ],
      [
        "expo-location",
        {
          "locationWhenInUsePermission": "Show nearby matches"
        }
      ],
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#FF6B6B"
        }
      ]
    ],
    "extra": {
      "eas": {
        "projectId": "your-project-id"
      }
    },
    "updates": {
      "url": "https://u.expo.dev/your-project-id"
    }
  }
}
```

### Push Notifications

```typescript
// Setup push notifications
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

async function registerForPushNotificationsAsync() {
  let token;

  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      alert('Failed to get push token for notifications!');
      return;
    }

    token = (await Notifications.getExpoPushTokenAsync()).data;

    // Send token to backend
    await apiClient.post('/api/notifications/register', {
      push_token: token,
      platform: Platform.OS
    });
  }

  if (Platform.OS === 'android') {
    Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF6B6B',
    });
  }

  return token;
}

// Handle notification received while app is foregrounded
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// Handle notification tap
useEffect(() => {
  const subscription = Notifications.addNotificationResponseReceivedListener(response => {
    const data = response.notification.request.content.data;

    if (data.type === 'new_match') {
      navigation.navigate('Match', { matchId: data.match_id });
    } else if (data.type === 'new_message') {
      navigation.navigate('Chat', { conversationId: data.conversation_id });
    }
  });

  return () => subscription.remove();
}, []);
```

### Native Performance Optimization

```typescript
// Use Hermes engine (enabled by default in Expo SDK 48+)
// Provides 50% faster startup, 40% smaller app size

// Optimize images
import { Image } from 'expo-image';  // Faster than react-native Image

<Image
  source={{ uri: profilePhotoUrl }}
  placeholder={require('./placeholder.png')}
  contentFit="cover"
  transition={200}
  cachePolicy="memory-disk"  // Aggressive caching
/>

// Lazy load screens
const MatchDetailScreen = lazy(() => import('./screens/MatchDetail'));

// Use FlashList instead of FlatList (10x faster for long lists)
import { FlashList } from "@shopify/flash-list";

<FlashList
  data={matches}
  renderItem={({ item }) => <MatchCard match={item} />}
  estimatedItemSize={200}
/>
```

### EAS Build & Deploy

```yaml
# eas.json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "simulator": false
      }
    },
    "production": {
      "autoIncrement": true,
      "cache": {
        "key": "production"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "your-apple-id@example.com",
        "ascAppId": "1234567890",
        "appleTeamId": "ABCDEFGHIJ"
      },
      "android": {
        "serviceAccountKeyPath": "./android-service-account.json",
        "track": "production"
      }
    }
  }
}
```

### CI/CD with GitHub Actions

```yaml
# .github/workflows/mobile-deploy.yml
name: Mobile Deploy

on:
  push:
    branches: [main]
    paths:
      - 'frontend/mobile/**'

jobs:
  build-ios:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - uses: expo/expo-github-action@v8
        with:
          expo-version: latest
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}
      - run: cd frontend/mobile && eas build --platform ios --non-interactive --no-wait
      - run: eas submit --platform ios --latest
```

## Consequences

### Positive
- **80% Code Reuse**: Between iOS and Android
- **50% Code Sharing**: With web app (hooks, API, types)
- **2x Development Speed**: Single team vs. two native teams
- **OTA Updates**: Fix bugs instantly, no 1-2 week App Store review
- **TypeScript**: Same language across frontend (web + mobile) and backend contracts
- **Cost Savings**: $200K/year savings vs. hiring separate iOS/Android teams
- **Rapid Iteration**: Hot reload during development, fast build times

### Negative
- **Performance**: 10-20% slower than native for complex animations
- **Native Modules**: Occasionally need custom native code (rare)
- **App Size**: 30-40MB vs. 10-15MB pure native
- **Bridge Overhead**: JavaScript bridge adds latency (mitigated by new architecture)
- **Expo Limitations**: Some native APIs require custom dev client

### Mitigation
- Use Expo's new architecture (Fabric + Turbo Modules) for near-native performance
- Eject to bare workflow only if absolutely needed (can always do later)
- Optimize bundle size with `expo-updates` selective asset loading
- Use native modules for performance-critical features (camera, video)

## Testing Strategy

```typescript
// Unit tests with Jest
import { render, screen } from '@testing-library/react-native';
import { MatchCard } from './MatchCard';

test('renders match card with name and bio', () => {
  const match = { id: '1', name: 'Alex', bio: 'Coffee lover' };
  render(<MatchCard match={match} />);
  expect(screen.getByText('Alex')).toBeTruthy();
  expect(screen.getByText('Coffee lover')).toBeTruthy();
});

// E2E tests with Detox
describe('Login Flow', () => {
  it('should login successfully', async () => {
    await element(by.id('email-input')).typeText('user@example.com');
    await element(by.id('password-input')).typeText('password123');
    await element(by.id('login-button')).tap();
    await expect(element(by.text('Matches'))).toBeVisible();
  });
});
```

## Related Decisions
- ADR-001: FastAPI backend (provides REST API for mobile)
- ADR-006: JWT authentication (mobile uses same auth flow)

## References
- [React Native Documentation](https://reactnative.dev/)
- [Expo Documentation](https://docs.expo.dev/)
- [EAS Build & Submit](https://docs.expo.dev/build/introduction/)
- [React Native New Architecture](https://reactnative.dev/docs/the-new-architecture/landing-page)

## Date
2025-11-17

## Authors
- Architect Agent
- Mobile Team
