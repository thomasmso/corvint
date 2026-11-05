#import "PQThemeStore.h"

static NSString *const kKey = @"puzzlequest.theme";

@implementation PQThemeStore

+ (instancetype)sharedStore
{
    static PQThemeStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQThemeStore alloc] init];
    });
    return shared;
}

- (NSInteger)selectedIndex
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setSelectedIndex:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
