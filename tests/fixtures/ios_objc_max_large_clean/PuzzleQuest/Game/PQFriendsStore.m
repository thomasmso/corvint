#import "PQFriendsStore.h"

static NSString *const kKey = @"puzzlequest.friends";

@implementation PQFriendsStore

+ (instancetype)sharedStore
{
    static PQFriendsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQFriendsStore alloc] init];
    });
    return shared;
}

- (NSInteger)count
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setCount:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
